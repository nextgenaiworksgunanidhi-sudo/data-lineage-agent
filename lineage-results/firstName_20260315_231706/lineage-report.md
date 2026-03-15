# Data Lineage Report

**Attribute:** firstName
**Query:** trace firstName from database to source
**Direction:** sink-to-source (DB → API)
**Repository:** spring-petclinic
**Date:** 2026-03-15

---

## Executive Summary

`firstName` is a person attribute stored in two database tables — `owners.first_name` and `vets.first_name` — both as `VARCHAR(30)`. It is defined once in the `Person.java` `@MappedSuperclass` base class and inherited by both `Owner.java` and `Vet.java` JPA entities, making it a shared field across two domain objects. The attribute flows inbound via HTML form submission at `POST /owners/new` and `POST /owners/{id}/edit`, is persisted through `OwnerRepository` via JPA, and is exposed outbound through six endpoints: owner detail/list Thymeleaf views, a REST JSON endpoint at `GET /vets`, and two Thymeleaf vet views. The only transformation applied is a JPA naming convention rename (`first_name` ↔ `firstName`) at the DB/ORM boundary — no custom mappers, stored procedures, or type conversions exist.

---

## Lineage Diagram

```
          ═══════════════════════════════════
                    ATTRIBUTE: firstName
                 Direction: DB → Source (↑)
          ═══════════════════════════════════

  ━━━━━━━━━━━━━━━━━━━━ PATH A: OWNER ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌───────────────────────────────────────┐
  │ [API]  POST /owners/new               │  ◄─ SOURCE (INBOUND)
  │        POST /owners/{ownerId}/edit    │     (HTML form input)
  └───────────────────────────────────────┘
    ↓ firstName (String) — @ModelAttribute form binding
  ┌───────────────────────────────────────┐
  │ [JAVA] OwnerController                │
  │        processCreationForm()          │
  │        processUpdateOwnerForm()       │
  └───────────────────────────────────────┘
    ↓ Owner.firstName (String) — JPA save()
    ↓ ── RENAME: firstName → first_name ──►
  ┌───────────────────────────────────────┐
  │ [ORM]  OwnerRepository                │
  │        save(Owner) → DB write         │
  └───────────────────────────────────────┘
    ↓ first_name (VARCHAR 30) — persisted
  ┌───────────────────────────────────────┐
  │ [DB]   owners.first_name              │  ◄─ SINK
  │        VARCHAR(30)                    │
  └───────────────────────────────────────┘
    ↑ first_name (VARCHAR 30) — JPA load
    ↑ ── RENAME: first_name → firstName ──►
  ┌───────────────────────────────────────┐
  │ [ORM]  Person.java (@MappedSuperclass)│
  │        field: firstName String        │
  │        @Column @NotBlank              │
  └───────────────────────────────────────┘
    ↑ firstName (String) — entity inheritance
  ┌───────────────────────────────────────┐
  │ [ORM]  Owner.java (@Entity "owners")  │
  │        inherits firstName from Person │
  └───────────────────────────────────────┘
    ↑ Optional<Owner>.firstName — query result
  ┌───────────────────────────────────────┐
  │ [ORM]  OwnerRepository                │
  │        findById(Integer)              │
  │        findByLastNameStartingWith()   │
  └───────────────────────────────────────┘
    ↑ Owner.firstName — put into ModelAndView / Model
  ┌───────────────────────────────────────┐
  │ [JAVA] OwnerController                │
  │        showOwner(ownerId)             │
  │        processFindForm(page, owner)   │
  └───────────────────────────────────────┘
    ↑ firstName rendered in template
  ┌───────────────────────────────────────┐
  │ [API]  GET /owners/{ownerId}          │  ◄─ SOURCE (OUTBOUND)
  │        GET /owners                    │     (Thymeleaf views)
  │        ownerDetails.html             │
  │        ownersList.html               │
  └───────────────────────────────────────┘

  ━━━━━━━━━━━━━━━━━━━━ PATH B: VET ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌───────────────────────────────────────┐
  │ [DB]   vets.first_name                │  ◄─ SINK
  │        VARCHAR(30) — seed data only   │
  └───────────────────────────────────────┘
    ↑ first_name (VARCHAR 30) — JPA load
    ↑ ── RENAME: first_name → firstName ──►
  ┌───────────────────────────────────────┐
  │ [ORM]  Person.java (@MappedSuperclass)│
  │        field: firstName String        │
  │        @Column @NotBlank              │
  └───────────────────────────────────────┘
    ↑ firstName (String) — entity inheritance
  ┌───────────────────────────────────────┐
  │ [ORM]  Vet.java (@Entity "vets")      │
  │        inherits firstName from Person │
  └───────────────────────────────────────┘
    ↑ Collection<Vet> / Page<Vet> — query result
  ┌───────────────────────────────────────┐
  │ [ORM]  VetRepository                  │
  │        findAll()                      │
  │        findAll(Pageable)              │
  └───────────────────────────────────────┘
    ↑ Vet.firstName — controller dispatch
           ┌──────────────────────────────────────────┐
           ↓ JSON path                HTML path       ↓
  ┌───────────────────┐       ┌────────────────────────┐
  │ [JAVA] VetCtrl    │       │ [JAVA] VetController   │
  │ showResources     │       │ showVetList(page,model) │
  │ VetList()         │       │                        │
  └───────────────────┘       └────────────────────────┘
    ↑ @ResponseBody JSON         ↑ Model attribute
  ┌───────────────────┐       ┌────────────────────────┐
  │ [API] GET /vets   │       │ [API] GET /vets.html   │
  │ JSON response     │       │ vetList.html           │  ◄─ SOURCE
  │ "firstName":"..." │       │ ${vet.firstName}       │    (OUTBOUND)
  └───────────────────┘       └────────────────────────┘

  ━━━━━━━━━━━━━━━━━━━━ SHARED BASE CLASS ━━━━━━━━━━━━━━━━━━━━━━━

  Person.java (@MappedSuperclass)
  └─ firstName (String) @Column @NotBlank
       ├─── inherited by ──► Owner.java  → owners.first_name
       └─── inherited by ──► Vet.java    → vets.first_name

LEGEND:
[API]  REST endpoint or web form (Thymeleaf / @ResponseBody)
[JAVA] Spring Java class/method (Controller)
[ORM]  JPA Repository or Entity (Hibernate-managed)
[DB]   Database table/column (MySQL / Postgres / H2)
══════════════════════════════════════════════════════
RENAME edges: only at DB↔ORM boundary (JPA convention)
              first_name (DB) ↔ firstName (Java)
```

---

## Layer by Layer Analysis

### API Layer

**Inbound (write) endpoints — firstName enters the system here:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /owners/new` | POST | Create new owner — firstName submitted via HTML form, bound via `@ModelAttribute` |
| `POST /owners/{ownerId}/edit` | POST | Update owner — firstName updated via HTML form |

**Outbound (read) endpoints — firstName exposed here:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /owners/{ownerId}` | GET | Owner detail view — `ownerDetails.html` renders `*{firstName + ' ' + lastName}` |
| `GET /owners` | GET | Owner list — `ownersList.html` renders `${owner.firstName + ' ' + owner.lastName}` |
| `GET /vets` | GET | REST JSON — Jackson serializes `Vet.firstName` as `"firstName": "..."` |
| `GET /vets.html` | GET | Vet list — `vetList.html:18` renders `${vet.firstName + ' ' + vet.lastName}` |

**Thymeleaf display-only (not editable):**
- `pets/createOrUpdatePetForm.html:17` — `${owner?.firstName}` in form header
- `pets/createOrUpdateVisitForm.html:26` — `${owner?.firstName}` in visit form header

**Validation:** `@NotBlank` (inherited from `Person.java`) enforced via Spring MVC `BindingResult` on form submit endpoints.

---

### Java Application Layer

**OwnerController** (`owner/OwnerController.java`)
- `processCreationForm(Owner, BindingResult, RedirectAttributes)` — receives firstName from POST form, delegates to `OwnerRepository.save()`
- `processUpdateOwnerForm(Owner, BindingResult, int, RedirectAttributes)` — receives updated firstName, delegates to `OwnerRepository.save()`
- `showOwner(int ownerId)` — loads Owner via `OwnerRepository.findById()`, puts into `ModelAndView`
- `processFindForm(int, Owner, BindingResult, Model)` — searches owners, puts list into `Model`

**VetController** (`vet/VetController.java`)
- `showResourcesVetList()` — returns `@ResponseBody Vets`, firstName serialized by Jackson to JSON
- `showVetList(int, Model)` — loads paginated vets, puts into `Model` for Thymeleaf

---

### ORM / Repository Layer

**Base class: `Person.java`** (`model/Person.java`)
- `@MappedSuperclass` — the canonical definition of `firstName`
- Field: `private String firstName` annotated `@Column @NotBlank`
- Accessors: `getFirstName()` / `setFirstName(String)`
- Inherited by `Owner.java` and `Vet.java`

**Owner.java** (`owner/Owner.java`)
- `@Entity @Table(name="owners")` — inherits `firstName` from `Person`
- JPA maps `firstName` → `owners.first_name` by naming convention

**Vet.java** (`vet/Vet.java`)
- `@Entity @Table(name="vets")` — inherits `firstName` from `Person`
- JPA maps `firstName` → `vets.first_name` by naming convention

**OwnerRepository** (`owner/OwnerRepository.java`)
- `findById(Integer)` → `Optional<Owner>` — loads single owner (including firstName)
- `findByLastNameStartingWith(String, Pageable)` → `Page<Owner>` — search (returns firstName)

**VetRepository** (`vet/VetRepository.java`)
- `findAll()` → `Collection<Vet>` — loads all vets (including firstName)
- `findAll(Pageable)` → `Page<Vet>` — paginated load

---

### Database Layer

| Table | Column | Type | Constraints | Notes |
|-------|--------|------|-------------|-------|
| `owners` | `first_name` | `VARCHAR(30)` / `TEXT` (Postgres) | none | Written via form POST; read via owner views |
| `vets` | `first_name` | `VARCHAR(30)` / `TEXT` (Postgres) | none | Seeded via `data.sql`; read-only via REST/Thymeleaf |

**SQL objects:** DDL schema only (`schema.sql` for MySQL, H2, Postgres). No stored procedures, triggers, or views reference `first_name`.

**Seed data:** `db/postgres/data.sql` and `db/h2/data.sql` contain explicit `INSERT INTO vets (first_name, ...)` and `INSERT INTO owners (first_name, ...)` statements.

---

## Findings Summary

| Item | Detail |
|------|--------|
| Total paths | 4 |
| Total hops | 22 |
| Layers involved | DB, ORM, JAVA, API |
| Transformations | RENAME: `first_name` → `firstName` (JPA read, both paths); RENAME: `firstName` → `first_name` (JPA write, Owner path) |
| Sensitive data | No |
| Multiple write paths | Yes — create (`POST /owners/new`) and update (`POST /owners/{id}/edit`) |
| Shared base class | `Person.java` @MappedSuperclass — single canonical definition for Owner + Vet |
| No stored procedures | All DB operations via JPA/Hibernate ORM |
| No custom mappers | No MapStruct or ModelMapper — direct JPA binding only |
| Validation | `@NotBlank` enforced on all write paths via Spring MVC BindingResult |

---

## Raw JSON Lineage

```json
{
  "lineage": {
    "attribute": "firstName",
    "direction": "sink-to-source",
    "sensitive": false,
    "total_hops": 22,
    "transformations": [
      {
        "type": "RENAME",
        "from": "first_name",
        "to": "firstName",
        "at": "DB → ORM boundary",
        "detail": "JPA snake_case to camelCase convention on read (both Owner and Vet paths)"
      },
      {
        "type": "RENAME",
        "from": "firstName",
        "to": "first_name",
        "at": "ORM → DB boundary",
        "detail": "JPA camelCase to snake_case convention on write (Owner path only)"
      }
    ],
    "paths": [
      {
        "path_id": 1,
        "type": "primary",
        "label": "Owner READ — DB to Thymeleaf view",
        "hops": [
          { "order": 1, "layer": "DB",   "component": "owners.first_name",                          "action": "STORE",   "detail": "VARCHAR(30), MySQL/Postgres/H2 schema" },
          { "order": 2, "layer": "ORM",  "component": "Person.java",                                "action": "READ",    "detail": "@MappedSuperclass — field firstName String @Column @NotBlank; RENAME: first_name → firstName" },
          { "order": 3, "layer": "ORM",  "component": "Owner.java",                                 "action": "READ",    "detail": "@Entity table=owners — inherits firstName from Person" },
          { "order": 4, "layer": "ORM",  "component": "OwnerRepository.findById(Integer)",          "action": "READ",    "detail": "Returns Optional<Owner> containing firstName" },
          { "order": 5, "layer": "JAVA", "component": "OwnerController.showOwner(int ownerId)",     "action": "READ",    "detail": "GET /owners/{ownerId} — puts Owner into ModelAndView" },
          { "order": 6, "layer": "API",  "component": "GET /owners/{ownerId}",                      "action": "EXPOSE",  "detail": "Thymeleaf ownerDetails.html — renders *{firstName + ' ' + lastName}" }
        ]
      },
      {
        "path_id": 2,
        "type": "secondary",
        "label": "Owner WRITE — form POST to DB (create)",
        "hops": [
          { "order": 1, "layer": "API",  "component": "POST /owners/new",                                                   "action": "RECEIVE", "detail": "HTML form input — firstName bound via @ModelAttribute; @NotBlank validation" },
          { "order": 2, "layer": "JAVA", "component": "OwnerController.processCreationForm(Owner, BindingResult, ...)",     "action": "WRITE",   "detail": "Spring MVC binds form fields to Owner.firstName" },
          { "order": 3, "layer": "ORM",  "component": "OwnerRepository.save(Owner)",                                       "action": "WRITE",   "detail": "JPA save — RENAME: firstName → first_name on DB write" },
          { "order": 4, "layer": "DB",   "component": "owners.first_name",                                                  "action": "STORE",   "detail": "VARCHAR(30) — value persisted to owners table" }
        ]
      },
      {
        "path_id": 3,
        "type": "secondary",
        "label": "Owner UPDATE — form POST to DB (edit)",
        "hops": [
          { "order": 1, "layer": "API",  "component": "POST /owners/{ownerId}/edit",                                             "action": "RECEIVE", "detail": "HTML form input — firstName bound via @ModelAttribute; @NotBlank validation" },
          { "order": 2, "layer": "JAVA", "component": "OwnerController.processUpdateOwnerForm(Owner, BindingResult, int, ...)",   "action": "WRITE",   "detail": "Spring MVC binds updated firstName to Owner" },
          { "order": 3, "layer": "ORM",  "component": "OwnerRepository.save(Owner)",                                             "action": "WRITE",   "detail": "JPA save — RENAME: firstName → first_name on DB write" },
          { "order": 4, "layer": "DB",   "component": "owners.first_name",                                                       "action": "STORE",   "detail": "VARCHAR(30) — updated value persisted to owners table" }
        ]
      },
      {
        "path_id": 4,
        "type": "secondary",
        "label": "Vet READ — DB to REST JSON + Thymeleaf",
        "hops": [
          { "order": 1, "layer": "DB",   "component": "vets.first_name",                                    "action": "STORE",   "detail": "VARCHAR(30) — seeded via db/postgres/data.sql and db/h2/data.sql" },
          { "order": 2, "layer": "ORM",  "component": "Person.java",                                        "action": "READ",    "detail": "@MappedSuperclass — field firstName String @Column @NotBlank; RENAME: first_name → firstName" },
          { "order": 3, "layer": "ORM",  "component": "Vet.java",                                           "action": "READ",    "detail": "@Entity table=vets — inherits firstName from Person" },
          { "order": 4, "layer": "ORM",  "component": "VetRepository.findAll()",                            "action": "READ",    "detail": "Returns Collection<Vet> or Page<Vet> containing firstName" },
          { "order": 5, "layer": "JAVA", "component": "VetController.showResourcesVetList()",               "action": "EXPOSE",  "detail": "GET /vets @ResponseBody — Jackson serializes Vet.firstName to JSON" },
          { "order": 6, "layer": "API",  "component": "GET /vets",                                          "action": "EXPOSE",  "detail": "REST JSON response — serialized as \"firstName\": \"<value>\"" },
          { "order": 7, "layer": "JAVA", "component": "VetController.showVetList(int page, Model model)",   "action": "EXPOSE",  "detail": "GET /vets.html — adds Page<Vet> to Model" },
          { "order": 8, "layer": "API",  "component": "GET /vets.html",                                     "action": "EXPOSE",  "detail": "Thymeleaf vetList.html:18 — renders ${vet.firstName + ' ' + vet.lastName}" }
        ]
      }
    ]
  }
}
```

---
*Generated by Data Lineage Agent System*
