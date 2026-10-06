# filtro-insta

MVP de **moderação pré-publicação** para imagens e vídeos, com uma interface que
simula o fluxo de criação de postagem e um backend que analisa o conteúdo antes
de permitir a publicação.

A primeira versão usa o modelo open source **NudeNet 3.4.2** para detectar
regiões explícitas em imagens. Vídeos são amostrados em intervalos configuráveis
e cada frame selecionado passa pelo mesmo detector.

## Fluxo

```text
Usuário escolhe mídia
        |
        v
Frontend React/Vite
        |
        v
POST /api/moderate
        |
        +--> imagem: NudeNet
        |
        +--> vídeo: OpenCV -> frames -> NudeNet
        |
        v
Política de decisão
  ALLOW / REVIEW / BLOCK
        |
        v
Interface mostra o resultado antes de "publicar"
```

## Decisões do MVP

- `ALLOW`: o detector não encontrou evidência suficiente para bloquear.
- `REVIEW`: há sinal relevante, mas abaixo do threshold de bloqueio.
- `BLOCK`: há detecção explícita com confiança alta.

Os thresholds atuais são **heurísticos** e servem apenas como ponto inicial.
Antes de qualquer uso real eles precisam ser calibrados com um conjunto de
validação representativo.

## Estrutura

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── moderation.py
│   │   └── policy.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── docs/
│   └── test-plan.md
├── .github/workflows/ci.yml
└── docker-compose.yml
```

## Rodando com Docker

Pré-requisito: Docker + Docker Compose.

```bash
docker compose up --build
```

Depois:

- frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- health check: http://localhost:8000/health

Na primeira construção do backend as dependências e o modelo podem levar algum
tempo para serem preparados.

## Rodando sem Docker

### Backend

Recomendado: Python 3.11.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

### Frontend

Recomendado: Node.js 20.

```bash
cd frontend
npm install
npm run dev
```

## API

### `POST /api/moderate`

Envie `multipart/form-data` com o campo `file`.

Exemplo:

```bash
curl -X POST http://localhost:8000/api/moderate \
  -F "file=@minha-imagem.jpg"
```

Resposta típica:

```json
{
  "filename": "minha-imagem.jpg",
  "media_type": "image",
  "decision": "BLOCK",
  "score": 0.91,
  "reasons": ["FEMALE_BREAST_EXPOSED:0.910"],
  "detections": [],
  "sampled_frames": 1,
  "processing_ms": 82.4
}
```

Os nomes das classes vêm do próprio modelo. Eles são usados internamente para
aplicar a política de moderação.

## Configuração

Variáveis do backend:

| Variável | Padrão | Descrição |
|---|---:|---|
| `MAX_UPLOAD_BYTES` | 104857600 | Limite de upload |
| `SAMPLE_EVERY_SECONDS` | 1.0 | Intervalo entre frames de vídeo |
| `MAX_VIDEO_SAMPLES` | 120 | Máximo de frames analisados |
| `DETECTOR_SCORE_THRESHOLD` | 0.25 | Pós-filtro mínimo das detecções |

Frontend:

| Variável | Padrão |
|---|---|
| `VITE_API_URL` | `http://localhost:8000` |

Veja também `backend/.env.example` e `frontend/.env.example`.

## Privacidade dos dados de teste

Não coloque imagens ou vídeos sensíveis no repositório.

As pastas `samples/` e `private_samples/` e extensões comuns de vídeo estão
ignoradas no Git. O plano de testes está em `docs/test-plan.md`.

No MVP:

- imagens são processadas diretamente pelo backend;
- vídeos usam um arquivo temporário local;
- o arquivo temporário é apagado após a análise;
- não existe persistência de uploads no projeto.

## Limitações atuais

Este é um detector visual de nudez, não um sistema completo de segurança de
conteúdo. Ainda faltam, por exemplo:

- classificação semântica de atos sexuais e contexto;
- OCR e análise de texto;
- áudio/transcrição;
- deduplicação e perceptual hashing;
- fila de revisão humana;
- calibração por categoria e por tipo de mídia;
- proteção contra adversarial examples;
- métricas em dataset de validação;
- análise de idade, que **não deve ser inferida apenas pela aparência visual**.

Para produção, uma boa evolução é combinar detector anatômico, classificador
semântico e uma faixa de revisão humana.

## NudeNet e licença

O backend depende de **NudeNet 3.4.2**, cujo repositório upstream é licenciado
sob **GNU AGPL v3**. Antes de distribuir ou operar este projeto como serviço,
revise as obrigações dessa licença e verifique se elas são compatíveis com o
produto pretendido.

## Sobre Instagram

Este projeto é uma demonstração independente e não é afiliado, patrocinado ou
aprovado pela Instagram ou pela Meta. A interface apenas simula um fluxo de
pré-publicação para fins de prototipagem.
