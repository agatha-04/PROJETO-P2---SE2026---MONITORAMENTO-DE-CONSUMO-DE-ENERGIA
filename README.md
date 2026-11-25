# Monitor de Consumo de Energia em Cargas CC (Raspberry Pi 4 + INA219)

Sistema embarcado desenvolvido com **Buildroot 2026.05.1** e **Docker** para monitoramento contínuo de tensão, corrente, potência e energia acumulada em cargas de corrente contínua (CC) utilizando o sensor **INA219** via barramento $\\text{I}^2\\text{C}$ na **Raspberry Pi 4 (4 GB)**.

## Identificação da Equipe

- **Grupo:** Quinteto
- **Integrantes:**
  - Agatha Fávaro - 231335
  - Cayo Almeida - 233514
  - Felipe Silone - 230418
  - Leonardo Nogueira - 231046
  - Leticia Moreiro - 233423
- **Repositório:** [PROJETO-P2---SE2026---MONITORAMENTO-DE-CONSUMO-DE-ENERGIA](https://github.com/agatha-04/PROJETO-P2---SE2026---MONITORAMENTO-DE-CONSUMO-DE-ENERGIA)

## 1\. Visão Geral e Requisitos Técnicos

O projeto foi projetado sob princípios de reprodutibilidade, isolamento de processos, operação 100% offline e tolerância a falhas:

* **Build Reproduzível:** Todo o sistema operacional, configurações de kernel, Device Tree e containers são construídos diretamente a partir deste repositório, sem alterações manuais pós-gravação no cartão microSD.
* **Versões Fixas:** Buildroot `2026.05.1`, imagem base Python `3.12.15-slim-bookworm`, Flask `3.1.3` e imagem da aplicação versionada como `energia-app:1.0` (sem uso da tag `latest`).
* **Operação Autônoma e Offline:** Inicialização automática sem necessidade de login ou acesso à Internet. A imagem Docker ARM64 é embutida no `rootfs` e o dashboard web não depende de CDNs externos.
* **Desempenho de Boot:** Tempo de *cold boot* (da energização até a primeira resposta válida do endpoint `/health`) inferior a $15,0\\text{ s}$.
* **Robustez e Persistência:** Banco de dados SQLite operando em modo `WAL` (*Write-Ahead Logging*) com retenção de amostras de 7 dias e preservação contínua do total de energia acumulada ($\\text{kWh}$).


## 2\. Arquitetura do Sistema

O sistema divide-se em três camadas principais:

1. **Hardware e Kernel Linux:** O driver nativo `ina2xx` é habilitado no kernel (`CONFIG\\\_SENSORS\\\_INA2XX=y`) e configurado via *Device Tree Overlay* (`ina219.dtbo`) no endereço $\\text{I}^2\\text{C}$ `0x40` com resistor *shunt* de $0,1\~\\Omega$ ($100000\~\\mu\\Omega$). As medições são expostas pelo kernel em `/sys/bus/i2c/devices/1-0040/hwmon/hwmon\\\*`.
2. **Camada de Containers (Docker Engine):** Uma única imagem ARM64 (`energia-app:1.0`) executa dois containers isolados que compartilham o volume persistente `/var/lib/energia`:

   * **`energia-coletor`:** Lê os arquivos do `sysfs` a cada $1\\text{ s}$, calcula a energia acumulada ($\\text{mW}\\cdot\\text{s} \\rightarrow \\text{kWh} = \\text{mWs} / (3,6 \\times 10^9)$) e grava no SQLite.
   * **`energia-web`:** Servidor Flask na porta `5000` (mapeada para a porta `80` do host) que fornece a interface gráfica, a API REST e o endpoint `/health`.
3. **Orquestração de Boot (`init`):** O BusyBox inicializa o daemon do Docker (`S60dockerd`) e executa o script customizado `S99energia`, responsável pelo provisionamento (`docker load`) no primeiro boot e pela subida automática dos containers.


## 3\. Montagem de Hardware e Segurança

### 3.1. Pinagem $\\text{I}^2\\text{C}$ (INA219 $\\leftrightarrow$ Raspberry Pi 4)

|Pino INA219|Pino Raspberry Pi 4|Pino Físico|
|-|-|:-:|
|`VCC`|$3,3\\text{ V}$|1|
|`GND`|`GND`|9|
|`SDA`|`GPIO2` (`SDA1`)|3|
|`SCL`|`GPIO3` (`SCL1`)|5|

### 3.2. Circuito de Potência (Medição em Série)

```text
Fonte CC (+) ---> \\\[ VIN+   INA219   VIN- ] ---> (+) CARGA (-) ---> Fonte CC (-)
                                                                        |
                                                             GND comum com RPi 4
```

### 3.3. Regras de Segurança

* Realize todas as conexões com a Raspberry Pi 4 e a fonte da carga **desligadas**.
* Respeite os limites máximos do módulo INA219: tensão de barramento de até $26\\text{ V}$ e corrente de até $3,2\\text{ A}$.
* O terminal negativo (`GND`) da fonte da carga deve estar interligado ao `GND` da Raspberry Pi 4 (referência comum).
* Nunca alimente cargas de potência pelos pinos de $5\\text{ V}$ da Raspberry Pi nem conecte tensão alternada da rede elétrica ($127\\text{ V}$ / $220\\text{ V}$).


## 4\. Estrutura do Repositório

```text
energia-rpi4/
├── application/                        # Código-fonte Python (coletor, API web e healthcheck)
│   ├── templates/
│   │   └── index.html                  # Dashboard web offline (sem CDN)
│   ├── coletor.py                      # Leitura do sysfs e gravação no SQLite (WAL)
│   ├── healthcheck.py                  # Verificação de saúde dos containers
│   ├── requirements.txt                # Dependências Python fixadas (Flask==3.1.3)
│   └── web.py                          # API REST e servidor web
├── buildroot-external/                 # Árvore BR2\\\_EXTERNAL (ENERGIA)
│   ├── board/
│   │   └── energia/
│   │       ├── rootfs-overlay/
│   │       │   ├── etc/
│   │       │   │   ├── init.d/
│   │       │   │   │   └── S99energia  # Script de provisionamento e autostart
│   │       │   │   ├── network/
│   │       │   │   │   └── interfaces  # Configuração de rede Ethernet
│   │       │   │   └── issue           # Banner de login do sistema
│   │       │   └── opt/
│   │       │       └── docker/         # Destino de energia-app.tar (gerado no build)
│   │       ├── config\\\_energia.txt      # Parâmetros de boot e habilitação do overlay I2C
│   │       ├── ina219-overlay.dts      # Código-fonte do Device Tree Overlay
│   │       ├── ina219.dtbo             # Binário compilado do Device Tree Overlay
│   │       ├── post-image-energia.sh   # Copia ina219.dtbo para a partição boot.vfat
│   │       └── users\\\_table.txt         # Criação do usuário padrão (aluno)
│   ├── configs/
│   │   └── energia\\\_rpi4\\\_defconfig      # Configuração reproduzível do Buildroot
│   ├── kernel-config/
│   │   └── energia.fragment            # Fragmento do kernel (INA2XX, cgroups, namespaces, NAT)
│   ├── Config.in
│   ├── external.desc
│   └── external.mk
├── docker/
│   └── Dockerfile                      # Definição da imagem ARM64 não-root
├── docs/                               # Manual técnico, tabelas de opções e evidências
│   └── images/                         # Fotos da montagem e capturas de tela
├── evidence/                           # Logs de boot, hashes SHA-256 e validações
├── scripts/                            # Automação de download, build e medição
│   ├── build-all.sh                    # Executa o build completo do zero
│   ├── build-container.sh              # Compila e exporta a imagem Docker ARM64
│   ├── get-buildroot.sh                # Baixa e extrai o Buildroot 2026.05.1
│   └── medir-boot.sh                   # Cronômetro de cold boot via /health
├── .gitignore
└── README.md
```

## 5\. Ambiente de Build e Compilação

### 5.1. Pré-requisitos no Host (Ubuntu 22.04 / 24.04)

Instale as ferramentas de compilação do Buildroot, o compilador de Device Tree e o suporte multiarquitetura (QEMU + Docker Buildx):

```bash
sudo apt update
sudo apt install -y build-essential git wget cpio unzip rsync file bc bison flex \\\\
  libssl-dev libncurses-dev python3 xz-utils tree mtools device-tree-compiler \\\\
  docker.io qemu-user-static binfmt-support

sudo usermod -aG docker "$USER"
```

> Observação: Reinicie a sessão do terminal após adicionar o usuário ao grupo `docker` para executar comandos Docker sem `sudo`. Nunca utilize `sudo` para compilar o Buildroot.

### 5.2. Compilação Automatizada (Build do Zero)

Para baixar o Buildroot `2026.05.1`, construir o container ARM64 (`energia-app:1.0`) e gerar a imagem final do cartão SD em um único fluxo:

```bash
cd \\\~/energia-rpi4
chmod +x scripts/\\\*.sh
./scripts/build-all.sh
```

### 5.3. Compilação Passo a Passo

Caso deseje executar cada etapa separadamente:

1. **Baixar o Buildroot `2026.05.1`:**

```bash
   ./scripts/get-buildroot.sh
   ```

2. **Construir e exportar a imagem Docker ARM64 para o overlay:**

```bash
   ./scripts/build-container.sh
   ```

3. **Carregar a configuração e compilar o sistema Linux:**

```bash
   cd \\\~/energia-rpi4/buildroot
   make O=../output BR2\\\_EXTERNAL=../buildroot-external energia\\\_rpi4\\\_defconfig
   make O=../output BR2\\\_EXTERNAL=../buildroot-external -j$(nproc)
   ```

Ao final do processo, a imagem estará disponível em `output/images/sdcard.img`.

## 6\. Gravação no Cartão microSD

1. Identifique o dispositivo correspondente ao cartão microSD (confirme atentamente pelo tamanho para não sobrescrever o disco do computador):

```bash
   lsblk -o NAME,SIZE,MODEL,TYPE,MOUNTPOINTS
   ```

2. Grave a imagem `sdcard.img` substituindo `/dev/sdX` pelo dispositivo correto:

```bash
   sudo dd if=\\\~/energia-rpi4/output/images/sdcard.img of=/dev/sdX bs=4M status=progress conv=fsync
   sync
   ```

3. *(Opcional)* Compactação e verificação de integridade (`SHA-256`):

```bash
   cd \\\~/energia-rpi4
   xz -T0 -k output/images/sdcard.img
   sha256sum output/images/sdcard.img.xz | tee docs/sdcard.img.xz.sha256
   ```

## 7\. Validação por Camadas

Com o cartão microSD inserido, o sensor INA219 conectado e o cabo Ethernet ligado na mesma rede do computador, energize a Raspberry Pi 4 (`hostname`: `energia-g01`, usuário: `aluno`).

### Camada 1: Kernel e Sensor INA219

Verifique se o driver `ina2xx` reconheceu o dispositivo no barramento $\\text{I}^2\\text{C}$:

```bash
dmesg | grep -i ina2
H=$(echo /sys/bus/i2c/devices/1-0040/hwmon/hwmon\\\*)
cat "$H/name"
for f in in0\\\_input in1\\\_input curr1\\\_input power1\\\_input; do echo "$f: $(cat "$H/$f")"; done
```

* **Esperado:** `name` retorna `ina219` e os valores em $\\text{mV}$, $\\text{mA}$ e $\\mu\\text{W}$ condizem com as medições aferidas no multímetro ($P = V \\times I$).

### Camada 2: Docker Engine e Containers

Confirme se os dois containers subiram automaticamente e estão saudáveis:

```bash
docker info
docker ps
docker inspect --format '{{.Name}}: {{.State.Health.Status}}' energia-web energia-coletor
```

* **Esperado:** Ambos os containers com status `Up` e saúde `healthy`.

### Camada 3: API e Endpoints Locais

Teste as respostas HTTP localmente na placa via `wget`:

```bash
wget -q -O - http://127.0.0.1/health
wget -q -O - http://127.0.0.1/api/atual
wget -q -O - http://127.0.0.1/api/energia
```

### Camada 4: Acesso pelo Navegador

Descubra o endereço IP da interface `eth0` na placa com `ip addr show eth0` e acesse no navegador do computador:

```text
http://<IP\\\_DA\\\_RASPBERRY>/
```

## 8\. Testes de Desempenho (Boot $< 15\\text{ s}$) e Robustez

### 8.1. Medição Oficial de Cold Boot

Após o primeiro boot (onde ocorre o provisionamento da imagem Docker), desligue totalmente a alimentação da placa e execute no computador host:

```bash
./scripts/medir-boot.sh <IP\\\_DA\\\_RASPBERRY>
```

Para análise interna das etapas de inicialização no kernel e no `S99energia`, execute na Raspberry Pi:

```bash
dmesg | grep ENERGIA
```

### 8.2. Recuperação de Falhas e Queda de Energia

* **Reinício automático de container:** Force o encerramento do processo web (`pkill -9 -f web.py`) e verifique com `docker ps` e `docker inspect --format '{{.RestartCount}}' energia-web` que o container é reiniciado automaticamente.
* **Integridade do banco após corte abrupto de energia:** Após desligar a fonte diretamente durante a operação, valide a integridade do arquivo SQLite:

```bash
  docker run --rm -v /var/lib/energia:/data energia-app:1.0 \\\\
    python -c "import sqlite3; print(sqlite3.connect('/data/energia.db').execute('PRAGMA integrity\\\_check').fetchone())"
  ```

* **Esperado:** `('ok',)` e preservação do valor acumulado em $\\text{kWh}$.

\---

## 9\. Segurança Implementada

|Container|Porta Exposta|Volumes Montados|Controles de Segurança|
|-|-|-|-|
|**`energia-coletor`**|Nenhuma|`/var/lib/energia:/data` (RW)<br>`/sys/bus/i2c/devices/1-0040:/ina:ro` (RO)|Execução como usuário não-root (`app`, UID `1000`), `--cap-drop ALL`, `--security-opt no-new-privileges`, `--read-only --tmpfs /tmp` e acesso restrito apenas ao diretório do sensor.|
|**`energia-web`**|`80:5000`|`/var/lib/energia:/data` (RW)|Execução como usuário não-root (`app`, UID `1000`), `--cap-drop ALL`, `--security-opt no-new-privileges`, `--read-only --tmpfs /tmp` e sem acesso ao hardware (`/sys`).|

## 10\. Diagnóstico Rápido (Troubleshooting)

|Sintoma|Causa Provável e Solução|
|-|-|
|`/sys/bus/i2c/devices/1-0040` ausente|Verifique `dtparam=i2c\\\_arm=on` e `dtoverlay=ina219` no `config\\\_energia.txt`, a presença de `ina219.dtbo` em `overlays/` na partição de boot e a fiação `SDA`/`SCL`.|
|Corrente lida com sinal negativo|Os terminais `VIN+` e `VIN-` do INA219 estão invertidos em relação à fonte e à carga.|
|`exec format error` ao iniciar container|A imagem foi compilada para `amd64`. Refaça o build com `--platform linux/arm64` via Docker Buildx + QEMU.|
|Endpoint `/health` retorna HTTP `503`|O coletor não gravou amostras nos últimos $5\\text{ s}$. Verifique `docker logs energia-coletor` e a montagem `/ina`.|
|Falta de espaço ao empacotar `rootfs`|Aumente o parâmetro `BR2\\\_TARGET\\\_ROOTFS\\\_EXT4\\\_SIZE` no `menuconfig` (ex.: `1G` ou `2G`).|
