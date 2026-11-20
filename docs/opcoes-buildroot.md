# Opções de configuração do Buildroot

As configurações foram realizadas pelo `menuconfig` do Buildroot. Para localizar cada opção, foi utilizada a pesquisa pelo símbolo (`/`), considerando que os caminhos dos menus podem variar entre versões.

| Caminho no menuconfig | Símbolo | Valor configurado | Motivo | Impacto |
|---|---|---|---|---|
| System configuration | `BR2_TARGET_GENERIC_HOSTNAME` | `energia-g05` | Identificar a placa na rede | Define o nome do dispositivo no sistema |
| System configuration | `BR2_ROOTFS_OVERLAY` | `$(BR2_EXTERNAL_ENERGIA_PATH)/board/energia/rootfs-overlay` | Copiar arquivos personalizados para o rootfs | Inclui arquivos e configurações adicionais no sistema |
| System configuration | `BR2_TARGET_GENERIC_ROOT_PASSWD` | Senha definida pelo grupo | Permitir login de manutenção | Habilita acesso administrativo ao sistema |
| System configuration | `BR2_ROOTFS_USERS_TABLES` | `$(BR2_EXTERNAL_ENERGIA_PATH)/board/energia/users_table.txt` | Criar e configurar usuários do sistema | Define usuários, grupos e permissões |
| Kernel → Linux Kernel | `BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES` | `$(BR2_EXTERNAL_ENERGIA_PATH)/kernel-config/energia.fragment` | Aplicar configurações adicionais ao kernel | Habilita recursos necessários ao INA219 e Docker |
| Target packages → Hardware handling | `BR2_PACKAGE_DOCKER_ENGINE` | `y` | Disponibilizar o Docker Engine | Permite executar e gerenciar contêineres |
| Target packages → Hardware handling | `BR2_PACKAGE_DOCKER_CLI` | `y` | Disponibilizar o cliente Docker | Permite executar comandos de gerenciamento do Docker |
| Filesystem images | `BR2_TARGET_ROOTFS_EXT4_SIZE` | `1G` | Definir o tamanho da imagem do sistema de arquivos | Reserva 1 GB para a imagem EXT4 |
| Target packages → Hardware handling → Firmware | `BR2_PACKAGE_RPI_FIRMWARE_CONFIG_FILE` | `$(BR2_EXTERNAL_ENERGIA_PATH)/board/energia/config_energia.txt` | Utilizar configuração personalizada da Raspberry Pi | Define os parâmetros de inicialização e carregamento dos overlays |
| System configuration | `BR2_ROOTFS_POST_IMAGE_SCRIPT` | `$(BR2_EXTERNAL_ENERGIA_PATH)/board/energia/post-image-energia.sh` seguido do script original `board/raspberrypi4-64/post-image.sh` | Executar o script personalizado antes do script original | Copia o overlay `ina219.dtbo` para a partição de boot |

## Observações

- O hostname configurado é `energia-g05`.
- O sistema de arquivos selecionado é EXT4, com tamanho de 1 GB.
- O arquivo `energia.fragment` contém configurações adicionais do kernel.
- O script `post-image-energia.sh` copia o overlay do INA219 para a partição de boot antes da execução do script original da Raspberry Pi.
- Os pacotes Docker Engine e Docker CLI foram habilitados para permitir o uso do Docker no sistema.
