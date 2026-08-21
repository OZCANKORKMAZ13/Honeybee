import pandas as pd

# --------------------------------------------------
# Response seçme kuralı (DEĞİŞMEDİ)
# --------------------------------------------------
def pick_response(series):
    # Tek kayıt varsa olduğu gibi
    if len(series) == 1:
        return series.iloc[0]

    # Birden fazla varsa ve (00) S/A varsa → onu seç
    sa = series[series.str.contains(r"\(00\)\s*S/A", na=False)]
    if not sa.empty:
        return sa.iloc[0]

    # Diğer durumlarda olduğu gibi (ilk)
    return series.iloc[0]


def process_dhs(df_raw: pd.DataFrame) -> pd.DataFrame:
    # --------------------------------------------------
    # 1️⃣ DATAFRAME KOPYASI
    # --------------------------------------------------
    df = df_raw.copy()
    df.columns = df.columns.str.strip()

    # --------------------------------------------------
    # 2️⃣ FullName ve StudentID
    # --------------------------------------------------
    df["FullName"] = df["Person Name"].str.strip()
    df["StudentID"] = df["Case #"].str.strip() + "/" + df["Person"]

    # --------------------------------------------------
    # 3️⃣ DateTime parse
    # --------------------------------------------------
    df["DateTime"] = pd.to_datetime(df["Date Time"], errors="coerce")
    df = df[df["DateTime"].notna()]

    df["Date"] = df["DateTime"].dt.strftime("%m/%d/%Y")
    df["Hour"] = df["DateTime"].dt.hour
    df["Time"] = df["DateTime"].dt.strftime("%H:%M")

    # --------------------------------------------------
    # 4️⃣ Morning / Afternoon
    # --------------------------------------------------
    df["Period"] = df["Hour"].apply(lambda x: "Morning" if x < 12 else "Afternoon")

    # --------------------------------------------------
    # 5️⃣ Trans Type normalize (IN / OUT)
    # --------------------------------------------------
    df["Trans_Clean"] = None
    df.loc[df["Trans Type"].str.contains("IN", case=False, na=False), "Trans_Clean"] = "IN"
    df.loc[df["Trans Type"].str.contains("OUT", case=False, na=False), "Trans_Clean"] = "OUT"

    # Geçersizleri at
    df = df[df["Trans_Clean"].notna()]
    
    # DD kayıtlarını seçimden çıkar
    df = df[~df["Response"].fillna("").str.contains(r"\(DD\)", na=False)]

    # --------------------------------------------------
    # 6️⃣ Kolon isimleri
    # --------------------------------------------------
    df["Time_Column"] = df["Period"] + "_" + df["Trans_Clean"]
    df["Response_Column"] = df["Time_Column"] + "_Response"

    # --------------------------------------------------
    # 7️⃣ Zaman sırasına göre sırala
    # --------------------------------------------------
    df = df.sort_values("DateTime")

    # --------------------------------------------------
    # ⏰ Time → her zaman en erken
    # --------------------------------------------------
    grouped_time = (
        df.groupby(
            ["Date", "StudentID", "FullName", "Time_Column"]
        )["Time"]
        .first()
        .reset_index()
    )

    # --------------------------------------------------
    # 📨 Response → (00) S/A kuralı
    # --------------------------------------------------
    grouped_response = (
        df.groupby(
            ["Date", "StudentID", "FullName", "Response_Column"]
        )["Response"]
        .apply(pick_response)
        .reset_index()
    )

    # --------------------------------------------------
    # 8️⃣ Pivot
    # --------------------------------------------------
    time_pivot = grouped_time.pivot(
        index=["Date", "StudentID", "FullName"],
        columns="Time_Column",
        values="Time"
    )

    response_pivot = grouped_response.pivot(
        index=["Date", "StudentID", "FullName"],
        columns="Response_Column",
        values="Response"
    )

    # --------------------------------------------------
    # 9️⃣ Birleştir
    # --------------------------------------------------
    final_df = pd.concat([time_pivot, response_pivot], axis=1).reset_index()
    final_df.columns.name = None
    required_columns = [
        "Morning_IN", "Morning_OUT",
        "Afternoon_IN", "Afternoon_OUT",
        "Morning_IN_Response", "Morning_OUT_Response",
        "Afternoon_IN_Response", "Afternoon_OUT_Response",
    ]

    for col in required_columns:
        if col not in final_df.columns:
            final_df[col] = pd.NA
    final_df = final_df.sort_values(by="FullName").reset_index(drop=True)

    return final_df
