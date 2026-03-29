# ============================================================
# PROJET : Customer & Marketing Performance Analysis
# OBJECTIF :
# Analyser le comportement d'achat des clients, construire des KPI
# business et segmenter les clients avec une approche RFM.
# DATASET :
# online_retail.csv
# ============================================================

import pandas as pd


# ----------------------------
# 1. CHARGEMENT DU DATASET
# ----------------------------
df = pd.read_csv("data/online_retail.csv")

print("Aperçu du dataset :")
print(df.head())

print("\nColonnes :")
print(df.columns.tolist())

print("\nDimensions :")
print(df.shape)


# ---------------------------
# 2. NETTOYAGE DES DONNÉES
# ---------------------------
print("\nValeurs manquantes :")
print(df.isna().sum())

# Conversion de la date
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Suppression des lignes sans CustomerID
df = df.dropna(subset=["CustomerID"])

# Conversion CustomerID en entier
df["CustomerID"] = df["CustomerID"].astype(int)

# Suppression des quantités ou prix négatifs / nuls
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

# Suppression des factures d'annulation (commencent souvent par C)
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

# Création du chiffre d'affaires par ligne
df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

# Création de colonnes temporelles
df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
df["InvoiceDay"] = df["InvoiceDate"].dt.date

print("\nDimensions après nettoyage :")
print(df.shape)


# ---------------------------
# 3. KPI BUSINESS PRINCIPAUX
# ---------------------------
total_revenue = df["TotalPrice"].sum()
total_customers = df["CustomerID"].nunique()
total_orders = df["InvoiceNo"].nunique()
average_order_value = total_revenue / total_orders

orders_per_customer = (
    df.groupby("CustomerID")["InvoiceNo"]
    .nunique()
    .mean()
)

print("\n========== KPI BUSINESS ==========")
print(f"Chiffre d'affaires total : {total_revenue:,.2f}")
print(f"Nombre de clients uniques : {total_customers}")
print(f"Nombre de commandes : {total_orders}")
print(f"Panier moyen : {average_order_value:,.2f}")
print(f"Fréquence moyenne d'achat par client : {orders_per_customer:.2f}")
print("=================================\n")


# ---------------------------
# 4. ANALYSES BUSINESS
# ---------------------------

# 4.1 Chiffre d'affaires par pays
revenue_by_country = (
    df.groupby("Country")["TotalPrice"]
    .sum()
    .sort_values(ascending=False)
)

print("Top 10 pays par chiffre d'affaires :")
print(revenue_by_country.head(10))

# 4.2 Chiffre d'affaires par mois
revenue_by_month = (
    df.groupby("YearMonth")["TotalPrice"]
    .sum()
    .sort_index()
)

print("\nChiffre d'affaires par mois :")
print(revenue_by_month)

# 4.3 Top produits par chiffre d'affaires
top_products = (
    df.groupby("Description")["TotalPrice"]
    .sum()
    .sort_values(ascending=False)
)

print("\nTop 10 produits par chiffre d'affaires :")
print(top_products.head(10))

# 4.4 Top clients par chiffre d'affaires
top_customers = (
    df.groupby("CustomerID")["TotalPrice"]
    .sum()
    .sort_values(ascending=False)
)

print("\nTop 10 clients par chiffre d'affaires :")
print(top_customers.head(10))


# ---------------------------
# 5. SEGMENTATION RFM
# ---------------------------
snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df.groupby("CustomerID").agg(
    Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
    Frequency=("InvoiceNo", "nunique"),
    Monetary=("TotalPrice", "sum")
).reset_index()

print("\nAperçu RFM :")
print(rfm.head())

# Scores RFM (1 à 4)
rfm["R_score"] = pd.qcut(
    rfm["Recency"],
    4,
    labels=[4, 3, 2, 1],
    duplicates="drop"
)

rfm["F_score"] = pd.qcut(
    rfm["Frequency"].rank(method="first"),
    4,
    labels=[1, 2, 3, 4],
    duplicates="drop"
)

rfm["M_score"] = pd.qcut(
    rfm["Monetary"],
    4,
    labels=[1, 2, 3, 4],
    duplicates="drop"
)

rfm["R_score"] = rfm["R_score"].astype(int)
rfm["F_score"] = rfm["F_score"].astype(int)
rfm["M_score"] = rfm["M_score"].astype(int)

rfm["RFM_Score"] = (
    rfm["R_score"].astype(str)
    + rfm["F_score"].astype(str)
    + rfm["M_score"].astype(str)
)


# ---------------------------
# 6. SEGMENTS CLIENTS
# ---------------------------
def assign_segment(row):
    if row["R_score"] >= 3 and row["F_score"] >= 3 and row["M_score"] >= 3:
        return "VIP"
    elif row["R_score"] >= 3 and row["F_score"] >= 2:
        return "Fidèles"
    elif row["R_score"] <= 2 and row["F_score"] >= 3:
        return "À réactiver"
    else:
        return "Occasionnels"


rfm["Segment"] = rfm.apply(assign_segment, axis=1)

print("\nRépartition des segments :")
print(rfm["Segment"].value_counts())

segment_summary = rfm.groupby("Segment").agg(
    Clients=("CustomerID", "count"),
    Recency_moyenne=("Recency", "mean"),
    Frequency_moyenne=("Frequency", "mean"),
    Monetary_moyenne=("Monetary", "mean")
).sort_values(by="Monetary_moyenne", ascending=False)

print("\nRésumé des segments :")
print(segment_summary)


# ---------------------------
# 7. INSIGHTS AUTOMATIQUES
# ---------------------------
print("\n========== INSIGHTS ==========\n")

top_country = revenue_by_country.index[0]
top_country_value = revenue_by_country.iloc[0]

top_product = top_products.index[0]
top_product_value = top_products.iloc[0]

vip_count = (rfm["Segment"] == "VIP").sum()
reactivate_count = (rfm["Segment"] == "À réactiver").sum()

print(f"Le chiffre d'affaires total est de {total_revenue:,.2f}.")
print(f"Le pays générant le plus de revenu est {top_country} avec {top_country_value:,.2f}.")
print(f"Le produit le plus rentable est '{top_product}' avec {top_product_value:,.2f} de revenu.")
print(f"Le portefeuille clients comprend {vip_count} clients VIP, à forte valeur.")
print(f"{reactivate_count} clients appartiennent au segment 'À réactiver', ce qui représente une opportunité de relance marketing.")

print("\n=============================\n")


# ---------------------------
# 8. EXPORTS POUR POWER BI
# ---------------------------
df.to_csv("online_retail_cleaned.csv", index=False)
rfm.to_csv("customer_rfm_segments.csv", index=False)
segment_summary.to_csv("segment_summary.csv")

print("Fichiers exportés :")
print("- online_retail_cleaned.csv")
print("- customer_rfm_segments.csv")
print("- segment_summary.csv")