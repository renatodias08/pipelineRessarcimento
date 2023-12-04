CREATE TABLE IF NOT EXISTS analise_predicao (numeroSinistro INTEGER, descricaoSinistro VARCHAR(5000), previsao VARCHAR(255), probabilidade VARCHAR(255), uuid VARCHAR(255), datahora datahora DATE DEFAULT current_timestamp);
CREATE TABLE IF NOT EXISTS analise_credito (numeroSinistro INTEGER, status VARCHAR(255), uuid VARCHAR(255), datahora DATE DEFAULT current_timestamp);
commit;
