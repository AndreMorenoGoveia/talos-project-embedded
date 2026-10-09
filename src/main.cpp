// Projeto Talos — cofre eletrônico com ESP32 DevKit V1.
// Especificação: monografia do Grupo 7 (PCS3848). Ligações de hardware no README.md.
#include <Arduino.h>
#include <Preferences.h>
#include <esp_sleep.h>
#include <esp_system.h>
#include <esp_rom_crc.h>
#include <driver/rtc_io.h>
#include <mbedtls/sha256.h>
#include <time.h>

// ---------------- Parâmetros configuráveis (Tabela 8) ----------------
constexpr uint32_t T_INAT    = 15000;  // ms, timeout de inatividade
constexpr uint32_t T_DESC    = 60000;  // ms, tempo sem interação até deep sleep
constexpr uint32_t T_ACIO    = 5000;   // ms, solenoide energizado (destravado)
constexpr uint32_t T_DEB     = 50;     // ms, debounce
constexpr uint32_t T_STEALTH = 3000;   // ms, segurar * + # para alternar stealth
constexpr uint32_t W_ADM     = 60000;  // ms, janela para troca de senha após autenticar
constexpr uint32_t T_LOCK    = 60;     // s, lockout base
constexpr uint32_t T_MAX     = 30 * 60;// s, teto do lockout
constexpr uint32_t W_REC     = 15 * 60;// s, janela de recorrência de lockouts
constexpr uint8_t  N_TENT    = 5;      // tentativas antes do lockout
constexpr bool     DESAFIO_CONTA_FALHA = false;  // erro no desafio conta como tentativa?
constexpr bool     TEM_SENSOR_PORTA    = false;  // reed switch não comprado; ligue quando instalar
// Bateria: 12 V (exigida pelo solenoide). Divisor R1 = 330k (topo), R2 = 100k (base).
constexpr float    V_LOW   = 10.5f;
constexpr float    BAT_DIV = (330.0f + 100.0f) / 100.0f;  // calibre com multímetro

// ---------------- Pinos ----------------
// Teclado 4x4 (fios 1..8 da esquerda p/ direita = L1..L4, C1..C4).
// Todos RTC GPIO: linhas ficam em HIGH e colunas acordam o chip (ext1 ANY_HIGH).
const uint8_t LINHAS[4]  = {27, 14, 13, 4};
const uint8_t COLUNAS[4] = {32, 33, 25, 26};
const char TECLAS[4][4] = {{'1', '2', '3', 'A'},
                           {'4', '5', '6', 'B'},
                           {'7', '8', '9', 'C'},
                           {'*', '0', '#', 'D'}};
constexpr char K_LIMPAR = '*', K_CONFIRMAR = '#', K_ADMIN = 'A';
constexpr uint16_t COMBO_STEALTH = (1 << 12) | (1 << 14);  // * e #

constexpr uint8_t PIN_TRANCA = 16;  // gate do MOSFET do solenoide (pull-down 10k no gate!)
constexpr uint8_t PIN_BUZZER = 17;  // base do NPN do buzzer ativo 5 V
constexpr uint8_t PIN_LED    = 2;   // LED azul da placa (indicador visual / desafio)
constexpr uint8_t PIN_PORTA  = 34;  // reed switch, LOW = fechada (pull-up externo)
constexpr uint8_t PIN_BAT    = 36;  // ADC1_CH0 (VP)

// RF-04: T = min(T_MAX, T_LOCK * 2^k)
constexpr uint32_t lockoutS(uint8_t k) { return (T_LOCK << k) < T_MAX ? (T_LOCK << k) : T_MAX; }
static_assert(lockoutS(0) == 60 && lockoutS(1) == 120 && lockoutS(10) == T_MAX, "backoff");

// ---------------- Persistência A/B (Cap. 9) ----------------
struct Cfg {
  uint32_t seq;          // "version": maior = mais recente
  uint8_t hash[32];      // SHA-256 da senha
  uint8_t stealth;
  uint8_t falhas;        // tentativas erradas consecutivas (persistido contra power-cycle)
  uint8_t lockouts;      // lockouts consecutivos na janela W_REC
  uint8_t bloqueado;     // 1 = em lockout (retomado após reset)
  uint32_t lastLockTs;   // time() do FIM do último lockout (janela W_REC conta a partir dele)
  uint32_t crc;
} cfg;
Preferences nvs;
bool ativaB;

uint32_t crcDe(const Cfg &c) { return esp_rom_crc32_le(0, (const uint8_t *)&c, offsetof(Cfg, crc)); }
bool leCopia(const char *k, Cfg &c) { return nvs.getBytes(k, &c, sizeof c) == sizeof c && c.crc == crcDe(c); }

void salvaCfg() {
  const char *k = ativaB ? "cfg_a" : "cfg_b";  // grava sempre na cópia inativa
  cfg.seq++;
  cfg.crc = crcDe(cfg);
  nvs.putBytes(k, &cfg, sizeof cfg);
  Cfg lida;
  if (leCopia(k, lida) && !memcmp(&lida, &cfg, sizeof cfg)) ativaB = !ativaB;
  else Serial.println("[NVS] falha na verificacao da escrita");
}

void hashSenha(const char *s, uint8_t out[32]) { mbedtls_sha256_ret((const uint8_t *)s, 6, out, 0); }

bool hashIgual(const uint8_t *a, const uint8_t *b) {  // tempo constante
  uint8_t d = 0;
  for (int i = 0; i < 32; i++) d |= a[i] ^ b[i];
  return d == 0;
}

void dorme(uint32_t s = 0);

void carregaCfg() {
  if (!nvs.begin("talos", false)) {  // sem NVS não há como validar senha: fica travado e tenta de novo
    Serial.println("[NVS] falha ao abrir, nova tentativa em 60 s");
    dorme(60);
  }
  Cfg a, b;
  bool va = leCopia("cfg_a", a), vb = leCopia("cfg_b", b);
  if (va && (!vb || a.seq >= b.seq)) { cfg = a; ativaB = false; }
  else if (vb) { cfg = b; ativaB = true; }
  else {  // ambas corrompidas/vazias: padrão de fábrica 000000
    Serial.println("[NVS] sem configuracao valida, usando padrao");
    memset(&cfg, 0, sizeof cfg);
    hashSenha("000000", cfg.hash);
    ativaB = false;
    salvaCfg();
    salvaCfg();
  }
}

// ---------------- Feedback: LED + buzzer (padrões on/off) ----------------
// Buzzer ativo só liga/desliga: "melodia" de sucesso = bipes crescentes.
const uint16_t P_CLIQUE[] = {40};
const uint16_t P_ERRO[]   = {80, 80, 80};
const uint16_t P_LEVE[]   = {30, 60, 30};
const uint16_t P_SUCESSO[] = {60, 60, 120, 60, 300};
const uint16_t P_BLOQUEIO[] = {1500};
const uint16_t P_BATERIA[] = {100, 100, 100, 100, 100, 100, 100, 100, 100};
const uint16_t P_PISCA2[] = {150, 150, 150};
#define PLAY(p, ...) toca(p, sizeof(p) / sizeof(p[0]), ##__VA_ARGS__)

uint16_t pad[48];
uint8_t padLen, padIdx;
uint32_t padT;
bool padLoop, padSom;

void saida(bool on) {
  digitalWrite(PIN_LED, on);
  digitalWrite(PIN_BUZZER, on && padSom && !cfg.stealth);
}
void toca(const uint16_t *p, uint8_t n, bool som = true, bool loop = false) {
  memcpy(pad, p, n * sizeof *p);
  padLen = n; padIdx = 0; padT = millis(); padLoop = loop; padSom = som;
  saida(true);
}
void tickPadrao() {
  if (padIdx >= padLen || millis() - padT < pad[padIdx]) return;
  padT = millis();
  if (++padIdx >= padLen) {
    if (!padLoop) { saida(false); return; }
    padIdx = 0;
  }
  saida(!(padIdx & 1));  // índices pares = ligado
}
void esperaPadrao() { while (padIdx < padLen && !padLoop) { tickPadrao(); delay(1); } }

// ---------------- Teclado com debounce (RF-01) ----------------
uint16_t varre() {
  uint16_t m = 0;
  for (int l = 0; l < 4; l++) {
    // Só a linha varrida é saída; as outras ficam em alta impedância para que duas
    // teclas na mesma coluna não curto-circuitem um GPIO em HIGH com outro em LOW.
    pinMode(LINHAS[l], OUTPUT);
    digitalWrite(LINHAS[l], HIGH);
    delayMicroseconds(10);
    for (int c = 0; c < 4; c++)
      if (digitalRead(COLUNAS[c])) m |= 1 << (l * 4 + c);
    pinMode(LINHAS[l], INPUT);
  }
  return m;
}

uint16_t bruto, estavel;
uint32_t brutoT, comboT;
bool comboFeito, ignoraSoltura;

void alternaStealth() {
  cfg.stealth ^= 1;
  salvaCfg();
  Serial.printf("Stealth %s\n", cfg.stealth ? "ON" : "OFF");
  PLAY(P_PISCA2, false);  // confirmação visual
}

// Retorna a tecla recém-pressionada (estável por T_DEB) ou 0. Segurar não repete.
// * e # só valem na soltura: assim o combo stealth (* + #, em qualquer ordem) nunca
// vira Limpar/Confirmar. ignoraSoltura vale até todas as teclas serem soltas.
char leTecla() {
  uint16_t m = varre();
  uint32_t agora = millis();
  if (m != bruto) { bruto = m; brutoT = agora; }

  if (agora - brutoT >= T_DEB && m != estavel) {
    uint16_t novas = m & ~estavel & ~COMBO_STEALTH, soltas = estavel & ~m & COMBO_STEALTH;
    estavel = m;
    if (estavel == COMBO_STEALTH) { comboT = agora; comboFeito = false; ignoraSoltura = true; }
    if (ignoraSoltura) soltas = 0;
    if (!estavel) ignoraSoltura = false;
    if (uint16_t b = novas ? novas : soltas) {
      int i = __builtin_ctz(b);
      return TECLAS[i / 4][i % 4];
    }
  }
  if (estavel == COMBO_STEALTH && !comboFeito && agora - comboT >= T_STEALTH) {
    comboFeito = true;
    alternaStealth();
  }
  return 0;
}

// ---------------- Máquina de estados (Cap. 6) ----------------
enum Estado { S1_ENTROPIA, S2_DESAFIO, S3_SENHA, S4_VALIDACAO, S5_ACESSO, S6_BLOQUEIO, S7_TRANCA, S8_TROCA };
Estado st;
char buf[6];
uint8_t len, d1, d2, passoTroca;
uint8_t novaHash[32];
uint32_t tEstado, tAtividade, tAuth;
bool autenticado, portaAbriu;

void entra(Estado e);

// Grava a tentativa ANTES de comparar e de qualquer sinal: cortar a energia ao ver o
// LED/buzzer de erro (bateria acessível, RF-10) não apaga a tentativa.
void contaTentativa() { cfg.falhas++; salvaCfg(); }

void bloqueia() {  // RF-04
  uint32_t agora = time(nullptr);  // relógio RTC: sobrevive ao deep sleep; zerado é tratado no setup
  bool naJanela = cfg.lockouts && agora - cfg.lastLockTs <= W_REC;  // conta do FIM do lockout anterior
  cfg.lockouts = naJanela ? min(cfg.lockouts + 1, 15) : 1;
  cfg.lastLockTs = agora + lockoutS(cfg.lockouts - 1);
  cfg.falhas = 0;
  cfg.bloqueado = 1;
  salvaCfg();
  entra(S6_BLOQUEIO);
}

void registraFalha() {  // cfg.falhas já incrementado e salvo por contaTentativa()
  Serial.printf("Falha %u/%u\n", cfg.falhas, N_TENT);
  PLAY(P_ERRO);
  if (cfg.falhas < N_TENT) entra(S1_ENTROPIA);
  else bloqueia();
}

void mostraDesafio() {  // d piscadas por dígito (0 = uma piscada longa), pausa, repete
  uint16_t p[48];
  uint8_t n = 0;
  for (uint8_t d : {d1, d2}) {
    if (d == 0) { p[n++] = 800; p[n++] = 250; }
    else for (uint8_t i = 0; i < d; i++) { p[n++] = 200; p[n++] = 250; }
    p[n - 1] = 1000;
  }
  p[n - 1] = 2500;
  toca(p, n, true, true);
}

void entra(Estado e) {
  esperaPadrao();  // deixa o bipe anterior terminar
  st = e;
  tEstado = millis();
  len = 0;
  switch (e) {
    case S1_ENTROPIA:
      // ponytail: esp_random sem Wi-Fi/BT é pseudoaleatório; basta para espalhar marcas.
      d1 = esp_random() % 10;
      d2 = esp_random() % 10;
      Serial.printf("S1/S2: desafio anti-marcas = %u %u\n", d1, d2);
      mostraDesafio();
      st = S2_DESAFIO;
      break;
    case S3_SENHA:
      Serial.println("S3: digite a senha (6 digitos) e #");
      PLAY(P_LEVE);
      break;
    case S4_VALIDACAO: break;  // tratado em valida()
    case S5_ACESSO:
      Serial.println("S5: acesso concedido");
      digitalWrite(PIN_TRANCA, HIGH);
      PLAY(P_SUCESSO);
      autenticado = true;
      tAuth = tAtividade = millis();
      portaAbriu = false;
      if (cfg.falhas) { cfg.falhas = 0; salvaCfg(); }
      break;
    case S6_BLOQUEIO: {  // teclas ignoradas: dorme só com o timer até o fim do lockout
      uint32_t agora = time(nullptr), dur = lockoutS(cfg.lockouts - 1);
      if (agora >= cfg.lastLockTs) {
        cfg.bloqueado = 0;
        salvaCfg();
        Serial.println("S6: fim do bloqueio");
        dorme();  // volta a acordar pelo teclado
      }
      if (cfg.lastLockTs - agora > dur) { cfg.lastLockTs = agora + dur; salvaCfg(); }  // relógio zerou: recomeça
      Serial.printf("S6: bloqueado por %u s\n", (unsigned)(cfg.lastLockTs - agora));
      PLAY(P_BLOQUEIO);
      esperaPadrao();
      dorme(cfg.lastLockTs - agora);
      break;
    }
    case S7_TRANCA:
      digitalWrite(PIN_TRANCA, LOW);  // solenoide NF: sem energia = travado
      Serial.println("S7: trancado");
      delay(100);  // assentamento mecânico da lingueta
      entra(S1_ENTROPIA);
      break;
    case S8_TROCA:
      passoTroca = 0;
      Serial.println("S8: troca de senha - digite a senha ATUAL e #");
      PLAY(P_LEVE);
      break;
  }
}

void valida() {  // S4
  entra(S4_VALIDACAO);
  uint8_t h[32];
  hashSenha(buf, h);
  memset(buf, 0, sizeof buf);
  contaTentativa();
  if (hashIgual(h, cfg.hash)) entra(S5_ACESSO);  // S5 zera cfg.falhas
  else registraFalha();
}

void passoTrocaSenha() {  // S8: atual -> nova -> repetição -> NVS
  uint8_t h[32];
  hashSenha(buf, h);
  memset(buf, 0, sizeof buf);
  len = 0;
  if (passoTroca == 0) {
    contaTentativa();
    if (!hashIgual(h, cfg.hash)) { registraFalha(); return; }
    cfg.falhas = 0;
    salvaCfg();
    Serial.println("S8: digite a NOVA senha e #");
  } else if (passoTroca == 1) {
    memcpy(novaHash, h, 32);
    Serial.println("S8: repita a nova senha e #");
  } else {
    if (hashIgual(h, novaHash)) {
      memcpy(cfg.hash, novaHash, 32);
      salvaCfg();
      Serial.println("[LOG] senha alterada");
      PLAY(P_SUCESSO);
    } else {
      Serial.println("S8: senhas nao conferem");
      PLAY(P_ERRO);
    }
    autenticado = false;
    entra(S1_ENTROPIA);
    return;
  }
  passoTroca++;
  PLAY(P_LEVE);
}

// ---------------- S0: deep sleep ----------------
void dorme(uint32_t s) {  // s > 0: acorda só pelo timer, após s segundos (lockout)
  Serial.printf("S0: deep sleep%s\n", s ? " (timer)" : "");
  padLen = 0;
  saida(false);
  digitalWrite(PIN_TRANCA, LOW);
  if (s) {
    esp_sleep_enable_timer_wakeup(s * 1000000ULL);
    Serial.flush();
    esp_deep_sleep_start();
  }
  uint64_t mascara = 0;
  for (uint8_t p : LINHAS) { pinMode(p, OUTPUT); digitalWrite(p, HIGH); gpio_hold_en((gpio_num_t)p); }
  for (uint8_t p : COLUNAS) {
    rtc_gpio_init((gpio_num_t)p);
    rtc_gpio_set_direction((gpio_num_t)p, RTC_GPIO_MODE_INPUT_ONLY);
    rtc_gpio_pullup_dis((gpio_num_t)p);
    rtc_gpio_pulldown_en((gpio_num_t)p);
    mascara |= 1ULL << p;
  }
  esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);  // mantém os pull-downs
  esp_sleep_enable_ext1_wakeup(mascara, ESP_EXT1_WAKEUP_ANY_HIGH);
  Serial.flush();
  esp_deep_sleep_start();
}

void checaBateria() {  // RF-11
  uint32_t mv = analogReadMilliVolts(PIN_BAT);
  float v = mv * BAT_DIV / 1000.0f;
  if (mv > 500 && v < V_LOW) {  // < 0,5 V no pino = divisor ausente (ex.: alimentado por USB)
    Serial.printf("Bateria baixa: %.2f V\n", v);
    PLAY(P_BATERIA);
    esperaPadrao();
  }
}

void setup() {
  setCpuFrequencyMhz(80);  // RNF-05: teclado e buzzer não precisam de 240 MHz
  Serial.begin(115200);
  pinMode(PIN_TRANCA, OUTPUT); digitalWrite(PIN_TRANCA, LOW);  // RNF-01: estado seguro
  pinMode(PIN_BUZZER, OUTPUT); digitalWrite(PIN_BUZZER, LOW);
  pinMode(PIN_LED, OUTPUT);    digitalWrite(PIN_LED, LOW);
  if (TEM_SENSOR_PORTA) pinMode(PIN_PORTA, INPUT);
  for (uint8_t p : LINHAS) { gpio_hold_dis((gpio_num_t)p); pinMode(p, INPUT); }
  for (uint8_t p : COLUNAS) { rtc_gpio_deinit((gpio_num_t)p); pinMode(p, INPUT_PULLDOWN); }

  carregaCfg();
  bruto = estavel = varre();  // a tecla que acordou o chip não conta como dígito
  ignoraSoltura = estavel;    // nem na soltura (* e #)
  tAtividade = millis();
  Serial.printf("\nTalos: boot (wake=%d, stealth=%u)\n", esp_sleep_get_wakeup_cause(), cfg.stealth);
  checaBateria();
  uint32_t agora = time(nullptr);
  if (!cfg.bloqueado && agora < cfg.lastLockTs) {  // relógio zerou (sem bateria): janela W_REC recomeça agora
    cfg.lastLockTs = agora;
    salvaCfg();
  }
  if (cfg.falhas >= N_TENT) bloqueia();  // energia cortada entre a 5ª tentativa e o lockout
  entra(cfg.bloqueado ? S6_BLOQUEIO : S1_ENTROPIA);  // reset no meio do lockout retoma o restante
}

void loop() {
  delay(1);  // cede ao idle task (WAITI) em vez de girar a CPU
  tickPadrao();
  char k = leTecla();
  uint32_t agora = millis();
  if (k || estavel) tAtividade = agora;

  if (st == S5_ACESSO) {  // RF-17
    bool fechada = TEM_SENSOR_PORTA && digitalRead(PIN_PORTA) == LOW;
    if (TEM_SENSOR_PORTA && !fechada) portaAbriu = true;
    if ((portaAbriu && fechada) || agora - tEstado >= T_ACIO) entra(S7_TRANCA);
    return;
  }

  if (agora - tAtividade >= T_DESC) dorme();  // RF-12
  // Acordou e ninguém respondeu ao desafio: dorme já, sem piscar/bipar até T_DESC.
  if (st == S2_DESAFIO && !len && agora - tAtividade >= T_INAT) dorme();
  if ((st == S3_SENHA || st == S8_TROCA || (st == S2_DESAFIO && len)) && agora - tAtividade >= T_INAT) {
    Serial.println("Timeout de inatividade");  // RF-02
    entra(S1_ENTROPIA);
    return;
  }
  if (!k) return;

  if (k == K_ADMIN && st != S8_TROCA && autenticado && agora - tAuth < W_ADM) { entra(S8_TROCA); return; }

  bool digito = k >= '0' && k <= '9';
  if (st == S2_DESAFIO) {  // RF-07: compara dígito a dígito
    if (k == K_LIMPAR) { len = 0; PLAY(P_CLIQUE); mostraDesafio(); return; }
    if (!digito) { PLAY(P_LEVE); return; }
    if (k - '0' != (len ? d2 : d1)) {
      Serial.println("Desafio incorreto");
      if (DESAFIO_CONTA_FALHA) { contaTentativa(); registraFalha(); }
      else { PLAY(P_ERRO); entra(S1_ENTROPIA); }
      return;
    }
    PLAY(P_CLIQUE);
    if (++len == 2) entra(S3_SENHA);
    return;
  }

  // S3 / S8: entrada de 6 dígitos
  if (digito) {
    if (len < 6) { buf[len++] = k; PLAY(P_CLIQUE); }
    else PLAY(P_LEVE);
  } else if (k == K_LIMPAR) {
    len = 0;
    memset(buf, 0, sizeof buf);
    PLAY(P_CLIQUE);
  } else if (k == K_CONFIRMAR) {
    if (len != 6) PLAY(P_LEVE);  // RF-15
    else if (st == S3_SENHA) valida();
    else passoTrocaSenha();
  } else {
    PLAY(P_LEVE);
  }
}
