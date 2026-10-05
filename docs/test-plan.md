# Plano de testes de moderação

O objetivo do MVP é medir **recall de conteúdo explícito** sem transformar toda
imagem com pele exposta em bloqueio.

## Conjuntos de teste

Mantenha os arquivos reais fora do Git. A pasta `private_samples/` já é
ignorada.

Crie um conjunto local com categorias como:

- conteúdo explicitamente nu que deve resultar em `BLOCK`;
- casos ambíguos que devem resultar em `REVIEW`;
- praia, piscina e roupa de banho que idealmente devem resultar em `ALLOW`;
- academia e torso exposto;
- arte, desenho, manequins e imagens médicas;
- baixa luz, blur, compressão e enquadramentos parciais;
- vídeos em que o frame explícito aparece por pouco tempo.

## Métricas

Registre pelo menos:

- verdadeiro positivo;
- falso negativo;
- falso positivo;
- verdadeiro negativo;
- latência média e p95;
- quantidade de frames analisados por vídeo.

Para um filtro pré-publicação, falsos negativos importam muito, mas aumentar a
sensibilidade sem uma faixa de `REVIEW` pode causar falsos positivos demais.

## Calibração

Os thresholds iniciais são heurísticos. Não trate `0.65` como uma verdade
universal. Monte um conjunto de validação representativo e ajuste os thresholds
antes de qualquer uso real.

## Privacidade

Não versione imagens ou vídeos sensíveis. Para o MVP, o backend processa o
arquivo em memória; vídeo usa arquivo temporário que é removido após a análise.
