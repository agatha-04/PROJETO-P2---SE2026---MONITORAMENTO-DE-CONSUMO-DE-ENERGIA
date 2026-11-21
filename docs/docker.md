# Containers: permissões e justificativas

| Container | Porta | Volumes | Permissões e justificativa |
|---|---|---|---|
| `energia-coletor` | nenhuma | `/var/lib/energia` (leitura e escrita), diretório do INA219 em `/sys` (somente leitura) | Usuário comum, `--cap-drop ALL`, sem `--privileged`. Só enxerga o diretório do sensor, não o `/sys` inteiro. |
| `energia-web` | 80 do host para 5000 | `/var/lib/energia` (leitura e escrita, necessário para o SQLite em modo WAL); `pwm0` em `/pwm` (leitura e escrita) | Usuário comum, `--cap-drop ALL`, sem `--privileged`. O diretório `pwm0` é montado para a API mudar o ângulo do servo escrevendo `duty_cycle`. O `S56pwm` libera escrita apenas nesse arquivo (`chmod 666`). A configuração do PWM (período, habilitação) é feita no host, e o container não consegue alterá-la. |
