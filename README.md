# Projeto Talos — Cofre Eletrônico com ESP32

Firmware para **ESP32 DevKit V1**, baseado na monografia do Grupo 7 (PCS3848). Todo o código está em `src/main.cpp`.

**Guias (PDF):** [montagem e operação](docs/Guia_Montagem_Talos.pdf) · [casos de teste](docs/Guia_Testes_Talos.pdf). Para regerar: `python3 docs/gerar_guia.py` e `python3 docs/gerar_testes.py` (precisam do `reportlab`).

## Compilar e gravar

```bash
pipx install platformio       # uma vez só (sudo apt install pipx)
pio run -t upload -t monitor  # compila (-O3), grava e abre o serial (115200)
```

Se a gravação travar em `Connecting...`, segure o botão **BOOT** da placa.

Uso de memória com -O3: Flash 23,8% (312 KB), RAM 7,1% (23 KB).

## Ligações

| Sinal | GPIO | Observação |
|---|---|---|
| Teclado fios 1–8 (L1..L4, C1..C4) | 32, 33, 25, 26, 27, 14, 12, 13 | em sequência D32 → D13, sem resistores. Se as teclas saírem espelhadas, troque `TECLADO_INVERTIDO` (padrão `true`: D32 = fio 8). Todas as teclas acordam o cofre se o eFuse de 3,3 V estiver gravado (veja abaixo) |
| Solenoide FEC-91 | 16 | via MOSFET logic-level (ex.: IRLZ44N), **resistor de 10k do gate ao GND** e **diodo 1N4007** em antiparalelo com a bobina |
| Buzzer ativo | 17 (TX2) | direto: perna longa (+) no TX2, curta (–) no GND |
| LED indicador | 2 | LED azul da placa; para ficar visível, ligue um LED externo (+220 Ω) no mesmo pino |
| Bateria (ADC, opcional) | 36 (VP) | divisor 330k (topo) / 100k (GND) |
| Display 6 dígitos TM1637 (a caminho) | DIO 18, CLK 19 | VCC no **3V3**, não no 5 V; ative `TEM_DISPLAY` quando ligar |
| Sensor de porta (opcional) | 39 (VN) | reed switch para GND + pull-up externo de 10k; ative `TEM_SENSOR_PORTA` |

Alimentação: **bateria de 9 V**: + no `VIN` e na fechadura, – no `GND`. Sem conversor de tensão.
O limiar de bateria fraca (`V_LOW = 7,0 V`) e a razão do divisor (`BAT_DIV`) ficam no topo do `main.cpp`. Calibre `BAT_DIV` com um multímetro.

## Teclado

| Tecla | Função |
|---|---|
| `0`–`9` | dígitos |
| `*` | Limpar |
| `#` | Confirmar |
| `C` | troca de senha: senha antiga + `#`, depois senha nova + `#` |
| `*` + `#` por 3 s | liga/desliga o modo stealth (sem som) |

## Uso

1. Aperte qualquer tecla para acordar.
2. **Desafio anti-marcas**: o LED/buzzer indica 2 dígitos, cada um com N piscadas (0 = uma piscada longa). O padrão repete por até 15 s; sem resposta, o cofre volta a dormir. Os dígitos também saem no serial.
3. Digite a senha (senha de fábrica: `000000`) e aperte `#`. Se errar, digite de novo (sem novo desafio).
4. O solenoide solta por 3 s (com um tiriri rápido), trava de novo e o cofre volta a dormir.

Depois de 5 erros, o cofre fica bloqueado por 60 s. Se houver novo bloqueio até 15 min depois do fim do anterior, o tempo dobra a cada vez, até 30 min. O bloqueio e o contador de erros ficam salvos na NVS, então resetar a placa não zera o bloqueio.

## eFuse da tensão da flash (placa do grupo: já gravado)

Para o D12 poder ficar em nível alto no deep sleep (e todas as teclas acordarem o cofre), a tensão da flash
precisa estar fixa em 3,3 V por eFuse. **Irreversível**; só para módulos com flash de 3,3 V, como o WROOM-32:

```bash
espefuse.py --port /dev/ttyUSB0 set_flash_voltage 3.3V
```

O firmware detecta o eFuse no boot (`D12 livre` / `D12 strapping` no serial). Sem ele, as 4 teclas ligadas ao D12 não acordam o cofre.
