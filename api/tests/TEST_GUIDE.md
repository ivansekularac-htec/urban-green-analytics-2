# 🧪 Urban Green Analytics - Testiranje ORM Modela i Pydantic Schema-eva

Sveobuhvatne instrukcije za testiranje integracije između SQLAlchemy ORM modela i Pydantic schema-eva.

## 📋 Kratka Provera (5-10 minuta)

### 1. Provera Import-a (bez potrebe za bazom)

```bash
cd api
python tests/test_integration.py
```

**Šta se testira:**
- ✅ Svi ORM modeli (13 modela) se mogu importovati
- ✅ Sve Pydantic scheme (Base/Create/Update/Response) se mogu importovati
- ✅ RoleBase, RoleUpdate, FarmUpdate schema validacija
- ✅ Field(max_length) constraints rade ispravno
- ✅ Svi schema-evi sa optional poljima funkcionišu
- ✅ Backward compatibility wrapper `schemas.py` radi

**Očekivani rezultat:**
```
✓ All ORM models imported successfully
✓ All Pydantic schemas imported successfully
✓ RoleBase schema validation works
✓ RoleUpdate schema works with optional fields
✓ Field max_length constraints work correctly
✓ FarmUpdate schema works with optional fields
✓ SensorUpdate schema handles enum fields
...
✓ ALL TESTS PASSED!
```

---

## 🗄️ Test Baze Podataka (5-10 minuta)

### Preduslov
Trebate da imate PostgreSQL pokrenutan sa `app` schema-om i svim tabelama iz `infra/postgres/init/`.

### 2. Provera Baze Podataka

```bash
cd api
python -m pytest tests/test_database.py -v
# ili direktno:
python tests/test_database.py
```

**Šta se testira:**
- ✅ Konektivnost sa PostgreSQL bazom
- ✅ Postojanje `app` schema-e
- ✅ Svih 13 tabela postoji (roles, users, farms, sensors, harvests, itd)
- ✅ Sve ključne kolone postoje
- ✅ Sve tabele imaju `created_at` i `updated_at` kolone
- ✅ Svi primary keys su pravilno konfigurisani
- ✅ Svi foreign key relationships su pravilno postavljeni

**Očekivani rezultat:**
```
✓ Database connection successful
✓ Schema 'app' exists
✓ All 13 expected tables exist
✓ All key columns exist in tables
✓ All 13 tables have created_at and updated_at columns
✓ All 13 tables have primary keys
✓ All foreign key relationships are properly configured
✓ ALL DATABASE TESTS PASSED!
```

---

## 🔗 Test ORM-Pydantic Integracije

### 3. Integracija ORM i Pydantic Schema-eva

```bash
cd api
python tests/test_orm_pydantic_integration.py
```

**Šta se testira:**
- ✅ ORM modeli se mogu konvertovati u Pydantic response schema-eve
- ✅ UserCreate schema ima sve potrebne polje
- ✅ FarmCreate validira sve polja
- ✅ SensorStatus enum radi između modela i schema-eva
- ✅ Harvest Decimal polja rade ispravno
- ✅ Update schema-evi podržavaju partial updates
- ✅ QualityGradeBase, RoleBase constraints rade
- ✅ Crop-CropCategory relacije rade
- ✅ UserRole relacije (globalne i farm-specifične) rade
- ✅ FarmCrop asocijacije rade
- ✅ Email validacija rade
- ✅ Svi Create schema-evi se mogu instancirati

**Očekivani rezultat:**
```
✓ ORM Role model converts to Pydantic schema
✓ UserCreate schema fields are correctly defined
✓ FarmCreate schema validates all fields correctly
✓ Sensor enum conversion works correctly
✓ Harvest Decimal handling works correctly
✓ Update schemas support partial updates correctly
✓ Schema validation constraints work correctly
...
✓ ALL ORM-PYDANTIC INTEGRATION TESTS PASSED!
```

---

## 🔄 Test Update Schema-eva (PATCH operacije)

### 4. Testiranje CRUD Update Schema-eva

```bash
cd api
python tests/test_update_schemas.py
```

**Šta se testira:**
- ✅ RoleUpdate - sve kombinacije polja
- ✅ FarmUpdate - sva polja sa svim tipovima (Decimal, Enum, int)
- ✅ UserUpdate - password, email, is_active update-ovanje
- ✅ SensorUpdate - status change operacije
- ✅ CropUpdate - category change
- ✅ HarvestUpdate - weight korekcije
- ✅ QualityGradeUpdate - modifikacije gracija
- ✅ SensorTypeUpdate - izmene tipova senzora
- ✅ GrowingSystemTypeUpdate
- ✅ FarmInfrastructureTypeUpdate
- ✅ CropCategoryUpdate
- ✅ FarmCropUpdate - životni ciklus
- ✅ UserRoleUpdate - permisije
- ✅ Max_length constraints u Update schema-evima
- ✅ Data type preservation (Decimal, Enum, int)

**Očekivani rezultat:**
```
✓ RoleUpdate supports all field combinations
✓ FarmUpdate handles all field combinations
✓ UserUpdate supports password and status changes
✓ SensorUpdate supports status changes
✓ CropUpdate supports category and field updates
✓ HarvestUpdate supports weight corrections
...
✓ ALL UPDATE SCHEMA TESTS PASSED!
```

---

## 🚀 Kompletan Test Setup (sa Pytest)

### Instalacija Pytest (ako nije već instaliran)

```bash
cd api
pip install pytest pytest-cov
```

### Pokretanje Svih Testova Odjednom

```bash
cd api
pytest tests/ -v
```

### Pokretanje Specifičnog Test Fajla

```bash
pytest tests/test_integration.py -v
pytest tests/test_database.py -v
pytest tests/test_orm_pydantic_integration.py -v
pytest tests/test_update_schemas.py -v
```

### Pokretanje Specifičnog Test Funkcije

```bash
pytest tests/test_integration.py::test_import_all_orm_models -v
pytest tests/test_database.py::test_database_connection -v
```

### Pokretanje sa Code Coverage

```bash
pytest tests/ --cov=app --cov-report=html
# Tada otvori: htmlcov/index.html
```

---

## 📊 Šta Svaki Test Proverava

| Test | Fajl | Funkcija | Što Testira |
|------|------|----------|-----------|
| **Import** | test_integration.py | test_import_all_orm_models | 13 ORM modela + 2 enum-a |
| **Schema Import** | test_integration.py | test_import_all_schemas | Svi Base/Create/Update/Response schema-evi |
| **Validacija** | test_integration.py | test_field_max_length_constraint | Field(max_length=...) constraints |
| **Database** | test_database.py | test_database_connection | PostgreSQL konektivnost |
| **Tabele** | test_database.py | test_all_tables_exist | Sve 13 tabela postoje |
| **Kolone** | test_database.py | test_table_columns | Ključne kolone u tabelama |
| **Timestamps** | test_database.py | test_timestamp_columns_exist | created_at, updated_at u svim tabelama |
| **FK Relacije** | test_database.py | test_foreign_key_relationships | Foreign keys između tabela |
| **ORM→Schema** | test_orm_pydantic_integration.py | test_role_model_to_schema | ORM u Pydantic konverzija |
| **Enumi** | test_orm_pydantic_integration.py | test_enum_usage_in_schemas | FarmStatus, SensorStatus enum-i |
| **Update** | test_update_schemas.py | test_role_update_all_combinations | Update schema-evi sa optional poljima |
| **Partial** | test_update_schemas.py | test_optional_fields_in_update_schemas | PATCH operacije sa delimičnim update-ima |

---

## ✅ Checklist Nakon Testiranja

- [ ] `test_integration.py` - SVI TESTOVI PROSLEDI
- [ ] `test_database.py` - SVI TESTOVI PROSLEDI (ako je baza dostupna)
- [ ] `test_orm_pydantic_integration.py` - SVI TESTOVI PROSLEDI
- [ ] `test_update_schemas.py` - SVI TESTOVI PROSLEDI
- [ ] Nema `ImportError` ili `AttributeError` grešaka
- [ ] `Field(max_length)` constraints se primenjuju na sve string polja
- [ ] Svi ORM modeli nasledjuju `(Base, TimestampMixin)`
- [ ] Svi schema-evi imaju `from_attributes=True` (za ORM konverziju)
- [ ] `app/schemas.py` backward compatibility wrapper je ažurirani

---

## 🔍 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pydantic'`

**Rešenje:**
```bash
cd api
pip install pydantic pydantic-settings email-validator
```

### Problem: `ModuleNotFoundError: No module named 'sqlalchemy'`

**Rešenje:**
```bash
cd api
pip install sqlalchemy
```

### Problem: `error: could not translate host name "localhost" to address`

**Rešenje:** Baza nije pokrenuta. Pokreni:
```bash
docker-compose up postgres -d
```

Tada čekaj ~5 sekundi da se baza inicijalizuje.

### Problem: `FATAL: Ident authentication failed for user "app_user"`

**Rešenje:** Proverite `.env` fajl da li ima tačnih kredencijala:
```
POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
DATABASE_URL=postgresql://app_user:app_password@localhost:5432/app_db
```

---

## 📝 Primer Manuelnog Testiranja

Ako hoćete da testiranje radite direktno u Python REPL-u:

```python
# 1. Test import svih modela
from app.models import Role, Farm, Sensor, Harvest, User
print("✓ ORM models imported")

# 2. Test import svih schema-eva
from app.schemas import RoleCreate, RoleUpdate, FarmCreate, FarmUpdate
print("✓ Pydantic schemas imported")

# 3. Test kreiranje schema instance
role = RoleCreate(name="Admin", description="Admin role")
print(f"✓ RoleCreate works: {role}")

# 4. Test Update schema sa optional poljima
update = RoleUpdate(name="Editor")
print(f"✓ RoleUpdate works: {update}")

# 5. Test max_length constraint
try:
    bad_role = RoleCreate(name="X" * 101)
except Exception as e:
    print(f"✓ max_length constraint works: {type(e).__name__}")

# 6. Test database connection
from app.database import engine
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print("✓ Database connection works")
```

---

## 📚 Struktura Testova

```
tests/
├── __init__.py
├── test_integration.py              # 14 testova - osnovni imports i validacija
├── test_database.py                 # 6 testova - baza podataka
├── test_orm_pydantic_integration.py # 12 testova - ORM↔Pydantic
└── test_update_schemas.py           # 15 testova - CRUD Update operacije
```

**Ukupno: 47 testova za kompletnu validaciju**

---

## 🎯 Sledeći Koraci

Nakon što su svi testovi prosledi:

1. **Kreiraj API endpointe** - GET, POST, PATCH, DELETE za svaku entitetu
2. **Testiraj CRUD operacije** - CREATE, READ, UPDATE, DELETE
3. **Integruj validaciju** - koristi Update schema-eve za PATCH
4. **Dokumentuj API** - generiši OpenAPI/Swagger dokumentaciju
5. **Deploy** - prebaci u produkciju sa svim testima

---

**Napisan:** 2026-06-12
**Verzija:** 1.0
**Status:** ✅ Kompletan i spreman za testiranje
