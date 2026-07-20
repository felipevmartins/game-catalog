# Prompt para Auditoria Independente Final

Audite adversarialmente a especificação Codex Game Catalog v1.3 deste pacote.

Verifique consistência cruzada entre decisões canônicas, schema, migrations, arquitetura Python, CLI, fontes, execução incremental, backup/restore, privacidade, testes e prova vertical. Não recomende novamente mudanças resolvidas sem apontar contradição concreta, arquivo e seção.

Procure especialmente regressões em: identidade estável de Release/Product após correção de data; regions; proveniência por registro; histórico de propriedade; disponibilidade corrente/histórica; score primário; selected_titles por Release; capacidades pessoais; recuperação de runs; triggers de cadeia; exportação de derivados não current.

Classifique cada achado como:

- Obrigatório para implementação — falha objetiva de integridade, identidade, recuperabilidade, privacidade ou implementabilidade;
- Recomendado pós-MVP — melhoria útil sem bloquear o catálogo pessoal;
- Não aplicável/excesso de complexidade — quando a proposta pressupõe escala distribuída ou produto público não requerido.

Para cada achado informe ID, severidade, evidência, documentos afetados, correção mínima e teste capaz de provar a correção. Execute buscas pelos termos do documento 29. Não declare aprovação para produção; conclua apenas se a especificação está ou não pronta para implementação vertical controlada.
