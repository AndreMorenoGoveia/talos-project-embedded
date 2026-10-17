// Projeto Talos — cofre eletrônico com ESP32 DevKit V1.
// Especificação: monografia do Grupo 7 (PCS3848). Ligações de hardware no README.md.
#include <Arduino.h>
#include <Preferences.h>
#include <esp_sleep.h>
#include <esp_system.h>
#include <esp_rom_crc.h>
#include <driver/rtc_io.h>
#include <soc/efuse_reg.h>
#include <mbedtls/sha256.h>
#include <time.h>

// ---------------- Parâmetros configuráveis (Tabela 8) ----------------
constexpr uint32_t T_INAT    = 15000;  // ms, sem tecla: descarta a entrada e entra em deep sleep (RF-02/RF-12)
constexpr uint32_t T_ACIO    = 3000;   // ms, solenoide energizado (destravado)
constexpr uint32_t T_DEB     = 50;     // ms, debounce
constexpr uint32_t T_STEALTH = 3000;   // ms, segurar * + # para alternar stealth
constexpr uint32_t T_LOCK    = 60;     // s, lockout base
constexpr uint32_t T_MAX     = 30 * 60;// s, teto do lockout
constexpr uint32_t W_REC     = 15 * 60;// s, janela de recorrência de lockouts
constexpr uint8_t  N_TENT    = 5;      // tentativas antes do lockout
constexpr bool     DESAFIO_CONTA_FALHA = false;  // erro no desafio conta como tentativa?
constexpr bool     TEM_SENSOR_PORTA    = false;  // reed switch não comprado; ligue quando instalar
constexpr bool     TRANCA_ATIVA_EM_HIGH = true;  // false para módulo relé que aciona com IN em LOW
constexpr bool     TEM_DISPLAY         = false;  // módulo TM1637 de 6 dígitos ainda não chegou; true ao ligar
constexpr uint8_t  BRILHO_DISPLAY      = 4;      // 0..7
constexpr bool     DEBUG_TECLADO       = false;  // imprime cada tecla lida (revela a senha: só p/ diagnóstico)
constexpr bool     TECLADO_INVERTIDO   = true;   // fios na ordem 8..1 (D32 = fio 8); false = ordem do guia
// Bateria de 9 V (alimenta o VIN e o solenoide). Divisor R1 = 330k (topo), R2 = 100k (base).
constexpr float    V_LOW   = 7.0f;
constexpr float    BAT_DIV = (330.0f + 100.0f) / 100.0f;  // calibre com multímetro

// ---------------- Pinos ----------------
// Teclado 4x4: fios 1..8 (da esquerda p/ direita, vendo de frente) em sequência nos pinos
// D32, D33, D25, D26, D27, D14, D12, D13 — sem resistores externos. Fios 1-4 são as linhas
// físicas do teclado e 5-8 as colunas; o firmware LÊ as linhas (pinos RTC com pull-down
// interno, acordam o chip via ext1 ANY_HIGH) e ENERGIZA as colunas.
// D12 é strapping (HIGH no reset = flash em 1,8 V, não boota). Com o eFuse que fixa a flash em
// 3,3 V gravado (espefuse.py set_flash_voltage 3.3V), ele vira pino comum e fica em HIGH no sono
// como os outros: todas as teclas acordam. Sem o eFuse, fica em LOW e as teclas ligadas a ele
// não acordam (3 6 9 # na ordem do guia, ou 4 5 6 B com TECLADO_INVERTIDO).
const uint8_t LINHAS[4]  = {27, 14, 12, 13};  // energizadas (fios 5..8, ou 4..1 se invertido)
const uint8_t COLUNAS[4] = {32, 33, 25, 26};  // lidas, acordam o chip (fios 1..4, ou 8..5 se invertido)
constexpr uint8_t PIN_STRAP = 12;
bool d12Livre() {  // eFuses XPD_SDIO_FORCE e XPD_SDIO_TIEH: flash fixa em 3,3 V, D12 ignorado no boot
  uint32_t r = REG_READ(EFUSE_BLK0_RDATA4_REG);
  return (r & EFUSE_RD_SDIO_FORCE) && (r & EFUSE_RD_SDIO_TIEH);
}
const char LAYOUT[4][4] = {{'1', '2', '3', 'A'},  // como as teclas aparecem no teclado
                           {'4', '5', '6', 'B'},
                           {'7', '8', '9', 'C'},
                           {'*', '0', '#', 'D'}};
char tecla(int energizada, int lida) {
  return TECLADO_INVERTIDO ? LAYOUT[3 - energizada][3 - lida] : LAYOUT[lida][energizada];
}
constexpr char K_LIMPAR = '*', K_CONFIRMAR = '#', K_ADMIN = 'C';  // C: trocar a senha
constexpr uint16_t COMBO_STEALTH = TECLADO_INVERTIDO ? (1 << 3) | (1 << 1)    // * e # (bit = energizada*4 + lida)
                                                     : (1 << 3) | (1 << 11);

constexpr uint8_t PIN_TRANCA = 16;  // IN do módulo relé (ou gate do MOSFET com pull-down 10k)
constexpr uint8_t PIN_BUZZER = 17;  // base do NPN do buzzer ativo 5 V
constexpr uint8_t PIN_LED    = 2;   // LED azul da placa (status: pisca junto com os bipes)
constexpr uint8_t PIN_PORTA  = 39;  // VN: reed switch, LOW = fechada (pull-up externo)
constexpr uint8_t PIN_BAT    = 36;  // ADC1_CH0 (VP)
// Módulo de 6 dígitos TM1637 alimentado em 3V3 (os pull-ups do módulo vão ao VCC dele;
// em 5 V eles jogariam 5 V nos GPIOs). Sem TEM_DISPLAY o desafio sai em piscadas/bipes.
constexpr uint8_t PIN_DIO = 18;
constexpr uint8_t PIN_CLK = 19;
const uint8_t POS_TM[6] = {2, 1, 0, 5, 4, 3};  // dígito da esquerda -> posição no TM1637 (padrão RobotDyn);
                                               // se os dígitos saírem embaralhados, ajuste aqui

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
  bool buz = digitalRead(PIN_BUZZER);
  digitalWrite(PIN_BUZZER, LOW);  // buzzer ligado durante a gravação aumenta a chance de erro na flash
  for (int tentativa = 1; tentativa <= 3; tentativa++) {  // flash pode corromper uma gravação: repete
    nvs.putBytes(k, &cfg, sizeof cfg);
    Cfg lida;
    if (leCopia(k, lida) && !memcmp(&lida, &cfg, sizeof cfg)) { ativaB = !ativaB; break; }
    Serial.printf("[NVS] falha na verificacao da escrita (tentativa %d/3)\n", tentativa);
  }
  digitalWrite(PIN_BUZZER, buz);
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
const uint16_t P_TRAVA[]  = {150};
const uint16_t P_ABRE[]   = {50, 35, 50, 35, 110};  // "tiriri" rápido ao abrir
// Som só ao digitar (e nas respostas ao que foi digitado), ao abrir, ao trancar e no bloqueio.
// Desafio, bateria fraca e avisos automáticos ficam só no LED.
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

// ---------------- Display TM1637 (RF-07: mostra o desafio e a senha) ----------------
uint8_t tela[6];                                                  // segmentos, da esquerda p/ direita
uint8_t enviada[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};        // último conteúdo enviado ao módulo

void tmNivel(uint8_t pino, bool alto) {  // dreno aberto: alto = solta o pino (pull-up do módulo)
  if (alto) pinMode(pino, INPUT);
  else { pinMode(pino, OUTPUT); digitalWrite(pino, LOW); }
  delayMicroseconds(5);
}
void tmInicio() { tmNivel(PIN_DIO, false); }  // DIO desce com CLK alto
void tmFim() { tmNivel(PIN_CLK, false); tmNivel(PIN_DIO, false); tmNivel(PIN_CLK, true); tmNivel(PIN_DIO, true); }
void tmByte(uint8_t b) {  // LSB primeiro; o ACK do TM1637 é ignorado
  for (int i = 0; i < 8; i++, b >>= 1) { tmNivel(PIN_CLK, false); tmNivel(PIN_DIO, b & 1); tmNivel(PIN_CLK, true); }
  tmNivel(PIN_CLK, false); tmNivel(PIN_DIO, true); tmNivel(PIN_CLK, true); tmNivel(PIN_CLK, false);
}
void tmComando(uint8_t c) { tmInicio(); tmByte(c); tmFim(); }

void enviaTela() {  // só fala com o módulo quando o conteúdo muda
  if (!TEM_DISPLAY || !memcmp(tela, enviada, 6)) return;
  memcpy(enviada, tela, 6);
  uint8_t pos[6];
  for (int i = 0; i < 6; i++) pos[POS_TM[i]] = tela[i];
  tmComando(0x40);  // escrita com endereço automático
  tmInicio(); tmByte(0xC0); for (uint8_t b : pos) tmByte(b); tmFim();
  tmComando(0x88 | BRILHO_DISPLAY);  // display ligado
}
uint8_t seg7(char c) {  // bits: dp g f e d c b a
  static const uint8_t num[] = {0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F};
  if (c >= '0' && c <= '9') return num[c - '0'];
  switch (c) {
    case '-': return 0x40; case '_': return 0x08; case 'A': return 0x77; case 'b': return 0x7C;
    case 'C': return 0x39; case 'E': return 0x79; case 'L': return 0x38; case 'n': return 0x54;
    case 'O': return 0x3F; case 'P': return 0x73; case 't': return 0x78; default: return 0;
  }
}
void preparaTela(const char *s) { for (int i = 0; i < 6; i++) tela[i] = seg7(s[i]); }
void mostra(const char *s) { preparaTela(s); enviaTela(); }

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
    if (DEBUG_TECLADO && m) {
      int i = __builtin_ctz(m);
      Serial.printf("[tecla] mascara=0x%04X -> '%c' (energizada %d = GPIO%d, lida %d = GPIO%d)\n", m,
                    tecla(i / 4, i % 4), i / 4, LINHAS[i / 4], i % 4, COLUNAS[i % 4]);
    }
    uint16_t novas = m & ~estavel & ~COMBO_STEALTH, soltas = estavel & ~m & COMBO_STEALTH;
    estavel = m;
    if (estavel == COMBO_STEALTH) { comboT = agora; comboFeito = false; ignoraSoltura = true; }
    if (ignoraSoltura) soltas = 0;
    if (!estavel) ignoraSoltura = false;
    if (uint16_t b = novas ? novas : soltas) {
      int i = __builtin_ctz(b);
      return tecla(i / 4, i % 4);
    }
  }
  if (estavel == COMBO_STEALTH && !comboFeito && agora - comboT >= T_STEALTH) {
    comboFeito = true;
    alternaStealth();
  }
  return 0;
}

// ---------------- Máquina de estados (Cap. 6) ----------------
enum Estado { S0_DESCANSO, S1_ENTROPIA, S2_DESAFIO, S3_SENHA, S4_VALIDACAO, S5_ACESSO, S6_BLOQUEIO, S7_TRANCA, S8_TROCA };
Estado st;
char buf[6];
uint8_t len, d1, d2, passoTroca;
uint32_t tEstado, tAtividade;
bool portaAbriu;

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

void registraFalha(Estado volta) {  // cfg.falhas já incrementado e salvo por contaTentativa()
  Serial.printf("Falha %u/%u\n", cfg.falhas, N_TENT);
  PLAY(P_ERRO);
  if (cfg.falhas < N_TENT) entra(volta);
  else bloqueia();
}

// Conteúdo dos displays derivado do estado (chamado a cada volta do loop).
void mostraDesafio() {  // sem display: d piscadas/bipes por dígito (0 = uma longa), pausa, repete
  uint16_t p[48];
  uint8_t n = 0;
  for (uint8_t d : {d1, d2}) {
    if (d == 0) { p[n++] = 800; p[n++] = 250; }
    else for (uint8_t i = 0; i < d; i++) { p[n++] = 200; p[n++] = 250; }
    p[n - 1] = 1000;
  }
  p[n - 1] = 2500;
  toca(p, n, false, true);  // só LED: sem bipe ao acordar
}

void atualizaTela() {
  char t[7] = "      ";
  if (st == S2_DESAFIO) { t[2] = '0' + d1; t[3] = '0' + d2; }
  else if (st == S3_SENHA || st == S8_TROCA)  // dígitos reais; vazio = "_" (senha) ou "-" (troca)
    for (int i = 0; i < 6; i++) t[i] = i < len ? buf[i] : (st == S3_SENHA ? '_' : '-');
  else if (st == S5_ACESSO) memcpy(t, " OPEn ", 6);
  preparaTela(t);
  if (st == S2_DESAFIO) for (int i = 0; i < len; i++) tela[2 + i] |= 0x80;  // ponto = dígito do desafio aceito
  enviaTela();
}

void entra(Estado e) {
  esperaPadrao();  // deixa o bipe anterior terminar
  st = e;
  tEstado = millis();
  len = 0;
  switch (e) {
    case S0_DESCANSO:
      dorme();  // não retorna
      break;
    case S1_ENTROPIA:
      // ponytail: esp_random sem Wi-Fi/BT é pseudoaleatório; basta para espalhar marcas.
      d1 = esp_random() % 10;
      d2 = esp_random() % 10;
      Serial.printf("S1/S2: desafio anti-marcas = %u %u\n", d1, d2);
      if (!TEM_DISPLAY) mostraDesafio();
      st = S2_DESAFIO;
      break;
    case S3_SENHA:
      Serial.println("S3: digite a senha (6 digitos) e #");
      PLAY(P_LEVE, false);
      break;
    case S4_VALIDACAO: break;  // tratado em valida()
    case S5_ACESSO:
      Serial.println("S5: acesso concedido");
      if (cfg.falhas || cfg.lockouts || cfg.lastLockTs || cfg.bloqueado) {  // acerto zera todas as punições
        cfg.falhas = cfg.lockouts = cfg.bloqueado = 0;  // grava antes de ligar tranca e buzzer
        cfg.lastLockTs = 0;
        salvaCfg();
      }
      digitalWrite(PIN_TRANCA, TRANCA_ATIVA_EM_HIGH);
      PLAY(P_ABRE);
      tAtividade = millis();
      portaAbriu = false;
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
      mostra(" bLOC ");
      PLAY(P_BLOQUEIO);
      esperaPadrao();
      dorme(cfg.lastLockTs - agora);
      break;
    }
    case S7_TRANCA:
      digitalWrite(PIN_TRANCA, !TRANCA_ATIVA_EM_HIGH);  // solenoide NF: sem energia = travado
      Serial.println("S7: trancado");
      PLAY(P_TRAVA);
      delay(100);  // assentamento mecânico da lingueta
      entra(S0_DESCANSO);
      break;
    case S8_TROCA:
      passoTroca = 0;
      Serial.println("S8: troca de senha - digite a senha ANTIGA e #");
      PLAY(P_LEVE, false);
      break;
  }
}

void valida() {  // S4
  entra(S4_VALIDACAO);
  uint8_t h[32];
  hashSenha(buf, h);
  memset(buf, 0, sizeof buf);
  contaTentativa();
  if (hashIgual(h, cfg.hash)) entra(S5_ACESSO);  // S5 zera falhas e o histórico de bloqueios
  else registraFalha(S3_SENHA);  // errou: digita a senha de novo, sem novo desafio
}

void passoTrocaSenha() {  // S8: senha antiga -> senha nova (# confirma) -> NVS
  uint8_t h[32];
  hashSenha(buf, h);
  memset(buf, 0, sizeof buf);
  len = 0;
  if (passoTroca == 0) {
    contaTentativa();
    if (!hashIgual(h, cfg.hash)) { registraFalha(S0_DESCANSO); return; }  // antiga errada conta como tentativa
    cfg.falhas = 0;
    salvaCfg();
    Serial.println("S8: digite a NOVA senha e #");
    passoTroca = 1;
    PLAY(P_TRAVA);  // 1 bipe: senha antiga aceita
    return;
  }
  memcpy(cfg.hash, h, 32);
  salvaCfg();
  Serial.println("[LOG] senha alterada");
  PLAY(P_SUCESSO);  // 3 bipes crescentes: senha nova salva
  esperaPadrao();
  entra(S0_DESCANSO);
}

// ---------------- S0: deep sleep ----------------
void dorme(uint32_t s) {  // s > 0: acorda só pelo timer, após s segundos (lockout)
  Serial.printf("S0: deep sleep%s\n", s ? " (timer)" : "");
  padLen = 0;
  saida(false);
  digitalWrite(PIN_TRANCA, !TRANCA_ATIVA_EM_HIGH);
  if (TEM_DISPLAY) tmComando(0x80);  // display desligado (o TM1637 guarda o estado no sleep)
  if (s) {
    esp_sleep_enable_timer_wakeup(s * 1000000ULL);
    Serial.flush();
    esp_deep_sleep_start();
  }
  uint64_t mascara = 0;
  for (uint8_t p : LINHAS) {  // em HIGH para acordar com tecla; o D12 só se o eFuse permitir
    pinMode(p, OUTPUT);
    digitalWrite(p, p != PIN_STRAP || d12Livre());
    gpio_hold_en((gpio_num_t)p);
  }
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
    mostra(" bAt  ");
    PLAY(P_BATERIA, false);  // só LED
    esperaPadrao();
  }
}

void setup() {
  setCpuFrequencyMhz(80);  // RNF-05: teclado e buzzer não precisam de 240 MHz
  Serial.begin(115200);
  pinMode(PIN_TRANCA, OUTPUT); digitalWrite(PIN_TRANCA, !TRANCA_ATIVA_EM_HIGH);  // RNF-01: estado seguro
  pinMode(PIN_BUZZER, OUTPUT); digitalWrite(PIN_BUZZER, LOW);
  pinMode(PIN_LED, OUTPUT);    digitalWrite(PIN_LED, LOW);
  if (TEM_SENSOR_PORTA) pinMode(PIN_PORTA, INPUT);
  if (TEM_DISPLAY) { tmNivel(PIN_CLK, true); tmNivel(PIN_DIO, true); }
  for (uint8_t p : LINHAS) { gpio_hold_dis((gpio_num_t)p); pinMode(p, INPUT); }
  for (uint8_t p : COLUNAS) { rtc_gpio_deinit((gpio_num_t)p); pinMode(p, INPUT_PULLDOWN); }

  carregaCfg();
  bruto = estavel = varre();  // a tecla que acordou o chip não conta como dígito
  ignoraSoltura = estavel;    // nem na soltura (* e #)
  tAtividade = millis();
  Serial.printf("\nTalos: boot (wake=%d, stealth=%u, D12 %s)\n", esp_sleep_get_wakeup_cause(), cfg.stealth,
                d12Livre() ? "livre: todas as teclas acordam" : "strapping: 4 teclas nao acordam");
  checaBateria();
  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_EXT1) PLAY(P_CLIQUE);  // bipe único ao acordar pelo teclado
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
  atualizaTela();
  char k = leTecla();
  uint32_t agora = millis();
  if (k || estavel) tAtividade = agora;

  if (st == S5_ACESSO) {  // RF-17
    bool fechada = TEM_SENSOR_PORTA && digitalRead(PIN_PORTA) == LOW;
    if (TEM_SENSOR_PORTA && !fechada) portaAbriu = true;
    if ((portaAbriu && fechada) || agora - tEstado >= T_ACIO) entra(S7_TRANCA);
    return;
  }

  if (agora - tAtividade >= T_INAT) {  // RF-02: descarta a entrada parcial e dorme
    if (len) Serial.println("Timeout de inatividade");
    entra(S0_DESCANSO);
  }
  if (!k) return;

  if (k == K_ADMIN && (st == S2_DESAFIO || st == S3_SENHA)) {  // RF-06: C inicia a troca de senha
    PLAY(P_CLIQUE);
    entra(S8_TROCA);
    return;
  }

  bool digito = k >= '0' && k <= '9';
  if (st == S2_DESAFIO) {  // RF-07: compara dígito a dígito
    if (k == K_LIMPAR) { len = 0; PLAY(P_CLIQUE); if (!TEM_DISPLAY) mostraDesafio(); return; }
    if (!digito) { PLAY(P_LEVE); return; }
    if (k - '0' != (len ? d2 : d1)) {
      Serial.println("Desafio incorreto");
      if (DESAFIO_CONTA_FALHA) { contaTentativa(); registraFalha(S1_ENTROPIA); }
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
