import pandas as pd

df = pd.read_csv("EGT209_T4_Group3_raw_data_wk2.csv")

# drop empty columns
df = df.drop(columns=["latitude", "longitude", "elevation", "status"])
df = df.drop(columns=["field4"])

# rename fields
df = df.rename(columns={"field1": "temperature", "field2": "humidity", "field3": "air_quality"})

# fix types
df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
df[["temperature", "humidity", "air_quality"]] = df[["temperature", "humidity", "air_quality"]].apply(pd.to_numeric, errors="coerce")

# handle missing values
df = df.dropna(subset=["created_at", "temperature", "humidity", "air_quality"])

# save
df.to_csv("clean_EGT209_T4_Group3_raw_data_wk2.csv", index=False)