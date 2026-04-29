# Databricks notebook source
# MAGIC %md
# MAGIC # Shared customer pool
# MAGIC
# MAGIC Defines `CUSTOMER_POOL` — a deterministic list of 150 synthetic customers.
# MAGIC Every channel notebook `%run`s this and samples 100 rows so customers
# MAGIC overlap across channels (which is what makes the 360 view interesting).

# COMMAND ----------

FIRST_NAMES = [
    "Alejandro", "Sofia", "Diego", "Camila", "Mateo", "Valentina", "Lucas",
    "Isabella", "Sebastian", "Gabriela", "Daniel", "Maria", "Andres", "Lucia",
    "Jorge", "Elena", "Carlos", "Victoria", "Miguel", "Laura", "Ricardo",
    "Natalia", "Eduardo", "Daniela", "Fernando", "Andrea", "Roberto", "Paula",
    "Javier", "Adriana", "Manuel", "Carolina", "Pablo", "Jimena", "Hector",
    "Ximena", "Antonio", "Patricia", "Raul", "Beatriz", "Oscar", "Diana",
    "Felipe", "Monica", "Adrian", "Silvia", "Gerardo", "Renata", "Hugo",
    "Mariana", "Emilio", "Cecilia", "Ivan", "Lorena", "Cesar", "Fernanda",
    "Arturo", "Vanessa", "Joaquin", "Karla", "Rodrigo", "Alicia", "Esteban",
    "Mercedes", "Tomas", "Rosa", "Vicente", "Claudia", "Nicolas", "Brenda",
    "Alberto", "Pilar", "Rafael", "Susana", "Gustavo", "Veronica", "Enrique",
    "Marta", "Julian", "Teresa", "Salvador", "Luisa", "Mario", "Olga",
    "Ramon", "Alma", "Federico", "Concepcion", "Bernardo", "Lupita", "Cristian",
    "Ana", "Bruno", "Carmen", "Dario", "Esmeralda", "Francisco", "Gloria",
    "Ignacio", "Hilda", "Jaime", "Itzel",
]

LAST_NAMES = [
    "Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Perez", "Sanchez",
    "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes", "Cruz",
    "Morales", "Ortiz", "Gutierrez", "Chavez", "Ramos", "Ruiz", "Alvarez",
    "Mendoza", "Vargas", "Castillo", "Jimenez", "Vasquez", "Romero", "Herrera",
    "Medina", "Aguilar", "Castro", "Vega", "Rojas", "Silva", "Contreras",
    "Salazar", "Soto", "Cervantes", "Navarro", "Campos", "Cordova", "Delgado",
    "Estrada", "Fuentes",
]

CATALOG = "miguel_usage_testing_catalog"
SCHEMA = "bnpl_customer_360"

CUSTOMER_POOL = []
for _i in range(150):
    _first = FIRST_NAMES[_i % len(FIRST_NAMES)]
    _last = LAST_NAMES[(_i * 7 + 3) % len(LAST_NAMES)]
    CUSTOMER_POOL.append({
        "customer_id": f"CUST{_i + 1:04d}",
        "first_name": _first,
        "last_name": _last,
        "email": f"{_first.lower()}.{_last.lower()}{_i + 1:03d}@paylater-demo.com",
    })

print(f"Customer pool initialized — {len(CUSTOMER_POOL)} synthetic profiles.")
print(f"Target: {CATALOG}.{SCHEMA}")
