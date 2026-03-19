# remove-white-border

Script para remover as bordas brancas de fotos digitalizadas

## Como utilizar:

# Processar uma pasta inteira (cria pasta "fotos_sem_borda" automaticamente)
`python remove_bordas.py --pasta ./fotos`

# Arquivo único
`python remove_bordas.py --arquivo scan.jpg`

# Definir pasta de saída personalizada
`python remove_bordas.py --pasta ./entrada --saida ./resultado`

# Bordas acinzentadas ou amareladas (scanner sujo) → aumenta tolerância
`python remove_bordas.py --pasta ./fotos --tolerancia 40`

# Manter uma margem ao redor do conteúdo
`python remove_bordas.py --pasta ./fotos --padding 10`

# Sobrescrever se já processou antes
`python remove_bordas.py --pasta ./fotos --sobrescrever`

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `--pasta` | caminho | — | Pasta com imagens para processar em massa |
| `--arquivo` | caminho | — | Arquivo de imagem único |
| `--saida` | caminho | `<entrada>_sem_borda` | Pasta de destino dos arquivos processados |
| `--tolerancia` | 0–255 | `20` | Sensibilidade para detecção de branco. Aumente para bordas acinzentadas ou amareladas |
| `--padding` | pixels | `2` | Margem extra para preservar ao redor do conteúdo após o corte |
| `--sobrescrever` | flag | `false` | Reprocessa arquivos que já existem na pasta de saída |

> `--pasta` e `--arquivo` são mutuamente exclusivos — use um ou outro.