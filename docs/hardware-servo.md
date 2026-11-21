# Hardware: servo MG996R medido pelo INA219

Substitui a seção 1.3 do guia (carga genérica). A carga é o servo, alimentado
pela placa com buck (12 V -> cerca de 6 V). O INA219 fica em série no +6 V do servo.

## Ligações

| # | De | Para |
|---|---|---|
| 1 | Borne V+ da placa (saída do buck) | INA219 VIN+ |
| 2 | INA219 VIN- | Servo, fio vermelho |
| 3 | Borne GND da placa | Servo, fio marrom ou preto |
| 4 | Borne de sinal da placa | Servo, fio laranja ou amarelo |
| 5 | Raspberry GPIO18 (pino 12) | Borne de sinal da placa |
| 6 | Raspberry GND (pino 6) | GND da placa |
| 7 | INA219 VCC | Raspberry 3,3 V (pino 1) |
| 8 | INA219 GND | Raspberry GND (pino 9) |
| 9 | INA219 SDA / SCL | GPIO2 (pino 3) / GPIO3 (pino 5) |

O fio do Arduino que ia ao borne de sinal deve ser removido. Duas saídas na mesma linha
brigam, e o Arduino entrega 5 V, que o GPIO da Raspberry não tolera.

## Antes de ligar o servo

1. Com o servo desconectado, ligue a fonte e meça a saída do buck. Ajuste para cerca de 6 V
   (o MG996R aceita de 4,8 a 7,2 V).
2. Confirme com o multímetro que a trilha de sinal da placa não tem pull-up para 5 V.
3. Confira o GND comum entre fonte, placa e Raspberry.
4. Limite do INA219: 26 V e cerca de 3,2 A. O MG996R travado chega perto de 2,5 A.
