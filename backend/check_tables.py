import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="cybershield_db",
    user="cybershield_user",
    password="cybershield_pass"
)
cur = conn.cursor()

tables = [
    "tbl_organization",
    "tbl_user",
    "tbl_login",
    "tbl_network_asset",
    "tbl_forensic_case",
    "tbl_network_event",
    "tbl_containment_action",
]

for tbl in tables:
    print(f"\n{'='*60}")
    print(f"  TABLE: {tbl}")
    print(f"{'='*60}")
    cur.execute("""
        SELECT
            ordinal_position,
            column_name,
            data_type,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    """, (tbl,))
    rows = cur.fetchall()
    if not rows:
        print("  [NOT FOUND]")
        continue
    print(f"  {'#':<4} {'Column':<25} {'Type':<20} {'Size':<8} {'Nullable':<10} {'Default'}")
    print(f"  {'-'*85}")
    for r in rows:
        pos, col, dtype, maxlen, nprec, nscale, nullable, default = r
        size = str(maxlen) if maxlen else (f"{nprec},{nscale}" if nprec else "-")
        default_short = (str(default)[:30] + "...") if default and len(str(default)) > 30 else str(default or "-")
        print(f"  {pos:<4} {col:<25} {dtype:<20} {size:<8} {nullable:<10} {default_short}")

    # FK info
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = %s;
    """, (tbl,))
    fks = cur.fetchall()
    if fks:
        print(f"\n  Foreign Keys:")
        for col, ftbl, fcol in fks:
            print(f"    {col} -> {ftbl}({fcol})")

conn.close()
print("\n\nDone.")
