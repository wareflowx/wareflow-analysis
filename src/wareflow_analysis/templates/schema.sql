-- Wareflow Analysis Schema
-- Core database schema

-- Products table
CREATE TABLE produits (
    no_produit INTEGER PRIMARY KEY,
    nom_produit TEXT,
    description TEXT,
    classe_produit TEXT,
    categorie_1 TEXT,
    categorie_2 TEXT,
    categorie_3 TEXT,
    etat TEXT,
    configuration TEXT,
    ean_alternatif TEXT
);

-- Movements table
CREATE TABLE mouvements (
    oid INTEGER PRIMARY KEY,
    no_produit INTEGER,
    nom_produit TEXT,
    type TEXT,
    site_source TEXT,
    zone_source TEXT,
    localisation_source TEXT,
    conteneur_source TEXT,
    site_cible TEXT,
    zone_cible TEXT,
    localisation_cible TEXT,
    conteneur_cible TEXT,
    quantite_uoi TEXT,
    quantite INTEGER,
    unite TEXT,
    date_heure DATETIME,
    usager TEXT,
    raison REAL,
    lot_expiration REAL,
    date_expiration REAL,
    date_heure_2 TEXT,
    FOREIGN KEY (no_produit) REFERENCES produits(no_produit)
);

-- Orders table
CREATE TABLE commandes (
    commande TEXT PRIMARY KEY,
    type_commande TEXT,
    demandeur TEXT,
    destinataire TEXT,
    no_destinataire INTEGER,
    priorite INTEGER,
    vague TEXT,
    date_requise DATETIME,
    lignes INTEGER,
    chargement TEXT,
    transporteur TEXT,
    etat_inferieur TEXT,
    etat_superieur TEXT,
    etat TEXT,
    statut_prepositionnement_max TEXT,
    statut_prepositionnement_actuel TEXT
);

-- Receptions table
CREATE TABLE receptions (
    no_reference INTEGER PRIMARY KEY,
    reception INTEGER,
    quantite_recue INTEGER,
    produit INTEGER,
    fournisseur TEXT,
    site TEXT,
    localisation_reception TEXT,
    date_reception DATETIME,
    utilisateur TEXT,
    etat TEXT,
    numero_lot REAL,
    date_expiration REAL,
    FOREIGN KEY (produit) REFERENCES produits(no_produit)
);

-- Indexes
CREATE INDEX idx_mouvements_produit ON mouvements(no_produit);
CREATE INDEX idx_mouvements_date ON mouvements(date_heure);
CREATE INDEX idx_mouvements_usager ON mouvements(usager);
CREATE INDEX idx_mouvements_type ON mouvements(type);
