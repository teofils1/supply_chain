Awesome—pharma supply chain + blockchain + ESP32 is a great fit. Below is a practical, opinionated feature backlog you can turn directly into tickets. I’ve split it by layers (domain, frontend, backend, IoT, blockchain, security/compliance, DevOps) and tagged scope: **\[MVP]**, **\[P2]**, **\[Later]**.

---

# Domain features (pharma-specific)

* **Serialization & identification**

  * **\[MVP]** GS1 identifiers (GTIN, Lot, Expiry, Serial) and SGTIN; support unit→case→pallet aggregation trees.
  * **\[P2]** GS1 DataMatrix (2D) and GS1-128 (1D) encoding/decoding; label generation.
  * **\[Later]** EPC/RFID (EPCIS events), NFC tags.

* **Regulatory flows**

  * **\[MVP]** Electronic pedigree (chain of custody) for each saleable unit and lot.
  * **\[P2]** DSCSA (US) & EU FMD alignment: pack status (active, decommissioned, dispensed, recalled), verification requests, returns verification.
  * **\[Later]** Suspect/illegitimate product investigation workflow.

* **Cold-chain & quality**

  * **\[MVP]** Temperature/humidity monitoring with excursion rules per product (e.g., 2–8 °C vaccines).
  * **\[P2]** Shock/light exposure tracking; excursion investigation & disposition.
  * **\[Later]** Stability budget tracking across the product lifetime.

* **Operational workflows**

  * **\[MVP]** Create product (SKU), create batch/lot, serialize packs, create shipment (pick/pack), handoff events (ship/receive), warehouse storage, retailer receipt.
  * **\[P2]** Returns & reverse logistics, recall execution (target list, confirmation), quarantine & release.
  * **\[Later]** Dispensing at pharmacy/hospital, kit assembly.

* **Search & reporting**

  * **\[MVP]** Trace by serial/lot/GTIN; shipment tracking; excursion report.
  * **\[P2]** Recall impact report; on-chain vs off-chain integrity report; SLA/lead time analytics.
  * **\[Later]** Predictive risk (excursion risk by lane/season).

---

# Data model (Django)

* **Core entities**

  * **\[MVP]** `Product(GTIN, name, form, strength, storage_range, …)`
  * **\[MVP]** `Batch(product, lot, expiry, mfg_date, status)`
  * **\[MVP]** `Pack(batch, serial, aggregation_parent, status, current_owner)`
  * **\[MVP]** `Shipment(ref, status, origin, destination, carrier, planned_at, …)`
  * **\[MVP]** `Event(kind, actor, time, location, subject_type [Pack/Shipment/Batch], subject_id, payload_json, offchain_hash, onchain_tx, block_no)`
  * **\[P2]** `Excursion(event, metric, threshold, observed, disposition)`
  * **\[P2]** `Attachment(file, sha256, linked_to)` (for CoAs, temp logs)
  * **\[Later]** `VerificationRequest`, `Recall`, `Investigation`

* **Roles/permissions**

  * **\[MVP]** Operator (create/update), Auditor (read + verify), Admin (all).
  * **\[P2]** Manufacturer, Shipper, Warehouse, Retailer as org roles with per-org tenancy.

---

# Backend APIs (DRF)

* **Auth**

  * **\[MVP]** `POST /api/auth/token/`, `POST /api/auth/refresh/`, `GET /api/auth/me/`

* **Products & batches**

  * **\[MVP]** `GET/POST /api/products/`, `GET/PUT /api/products/{id}/`
  * **\[MVP]** `GET/POST /api/batches/`, `GET/PUT /api/batches/{id}/`

* **Serialization & aggregation**

  * **\[MVP]** `POST /api/packs/serialize` (bulk serials for a batch)
  * **\[MVP]** `POST /api/packs/aggregate` (assign children to parent case/pallet)
  * **\[MVP]** `GET /api/packs/{id or serial}`

* **Shipments**

  * **\[MVP]** `GET/POST /api/shipments/`, `GET/PATCH /api/shipments/{id}`
  * **\[MVP]** `POST /api/shipments/{id}/add-packs`, `POST /api/shipments/{id}/dispatch`, `POST /api/shipments/{id}/receive`

* **Events & trace**

  * **\[MVP]** `GET/POST /api/events/` (filter by product/batch/serial/shipment/date)
  * **\[MVP]** `GET /api/trace/serial/{sgtin}` (timeline, owners, integrity)
  * **\[P2]** `POST /api/events/verify` (recompute hash vs chain)

* **IoT ingestion (ESP32)**

  * **\[MVP]** `POST /api/iot/telemetry` (device\_id, signed payload, metrics)
  * **\[MVP]** `POST /api/iot/event` (scan/scan+measure → creates Event + optional Excursion)
  * **\[P2]** `POST /api/iot/provision` (issue device credentials), `GET /api/iot/ota/latest`

* **Compliance**

  * **\[P2]** `POST /api/verify/pack` (DSCSA/FMD style verify), `POST /api/returns/verify`

---

# Frontend (Angular 20 + PrimeNG + Tailwind)

* **Navigation & guard**

  * **\[MVP]** Auth guard on `/`; login at `/login`; toolbar shows Login/Logout.
  * **\[MVP]** Role-based menu (Operator, Auditor, Admin).

* **Pages**

  * **\[MVP]** **Dashboard**: KPIs (in-transit shipments, excursions, items at risk).
  * **\[MVP]** **Products** `/products`: list/detail; batches tab; storage range badges.
  * **\[MVP]** **Batches** `/batches`: list/detail; serialize packs; print labels (QR/DataMatrix).
  * **\[MVP]** **Packs** `/packs`: search by serial/GTIN/lot; status; aggregation tree viewer.
  * **\[MVP]** **Shipments** `/shipments`: list/detail; add packs; dispatch/receive wizard; map trace.
  * **\[MVP]** **Events** `/events`: timeline filterable; integrity badge (on-chain anchored?).
  * **\[MVP]** **Trace** `/trace/:serial`: end-to-end chain of custody + sensor overlays.
  * **\[P2]** **Excursions** `/excursions`: triage board, disposition workflow.
  * **\[P2]** **IoT Devices** `/devices`: register/provision, status, last telemetry, OTA.
  * **\[P2]** **Recalls** `/recalls`: target list upload, outreach tracking.
  * **\[Later]** **Investigations** `/investigations`, **Dispense** `/dispense`.

* **UX components**

  * **\[MVP]** GS1 DataMatrix/QR generator & scanner (webcam/mobile); Badge/Severity chips.
  * **\[MVP]** Aggregation tree (case/pallet expanders); PrimeNG Timeline for events.
  * **\[P2]** Map widget (leaflet) for shipment path; sparkline telemetry charts.
  * **\[Later]** Offline PWA scan & queue (for poor connectivity).

---

# ESP32 integration (devices & edge)

* **Hardware & sensors**

  * **\[MVP]** Temperature & humidity (SHT31/DS18B20), battery voltage; optional GPS (u-blox) via UART.
  * **\[P2]** Accelerometer (shock), light sensor (exposure), BLE scanner for tags.

* **Firmware features**

  * **\[MVP]** Secure provisioning (per-device key/cert or token), time sync, store-and-forward buffer.
  * **\[MVP]** Periodic telemetry (configurable), event-based push (door open, temp excursion).
  * **\[MVP]** Payload signing (Ed25519) + SHA-256 on sample windows; HTTPS (mTLS if certs).
  * **\[P2]** On-device hash of canonicalized event JSON for anchoring hints; BLE/NFC read of pack IDs.
  * **\[P2]** OTA updates (signed firmware), remote config (sampling rate, thresholds).
  * **\[Later]** Edge rules (excursion detection locally), GNSS assisted geofencing.

* **Device lifecycle**

  * **\[MVP]** Register → Provision → Attach to shipment → In-transit → Return/service.
  * **\[P2]** Calibration records & certificates linked to device.

---

# Blockchain anchoring

* **Smart-contract interface**

  * **\[MVP]** `anchorEvent(hash, ref)`; `getEvent(ref)` minimal registry.
  * **\[P2]** Anchor batch commitments for high-volume events; Merkle roots for daily rolls.
  * **\[Later]** Cross-chain anchoring / L2 batching; on-chain dispute markers.

* **Backend service**

  * **\[MVP]** Compute SHA-256 of canonical JSON for every Event; send tx; store tx hash + block.
  * **\[MVP]** Retry & reconciliation job (confirm finality; mark integrity status).
  * **\[P2]** Gas/fee management; provider failover; monitoring & alerts.

* **Frontend**

  * **\[MVP]** Integrity badge (Pending/Anchored/Failed) + link to block explorer.
  * **\[P2]** “Verify now” button (recompute & compare), bulk verification on traces.

---

# Security, audit, and compliance (pharma/GxP)

* **Access & identity**

  * **\[MVP]** JWT auth (done), role-based access (RBAC).
  * **\[P2]** 2FA for privileged roles; per-org tenancy; device tokens rotation.

* **Audit & e-signatures**

  * **\[MVP]** Immutable audit log of all CRUD + event anchoring refs.
  * **\[P2]** 21 CFR Part 11-style e-sign on critical actions (release, excursion disposition).
  * **\[P2]** Read-only “Auditor mode” UI & export packages (PDF/CSV + hash manifests).

* **Data protection**

  * **\[MVP]** TLS everywhere, encryption at rest for secrets; server-side hashing of attachments.
  * **\[P2]** Field-level encryption for sensitive lots/customers; key rotation (KMS).
  * **\[Later]** Data retention policies, legal hold, anonymized analytics.

---

# Background jobs & integrations

* **Jobs**

  * **\[MVP]** On-chain reconciliation; telemetry aggregation; excursion detection.
  * **\[P2]** Email/SMS alerts (excursions, delays); scheduled integrity audits.
  * **\[Later]** Carrier ETA ingestion; weather lane risk.

* **Standards & external**

  * **\[P2]** EPCIS 1.2/2.0 import/export (event mapping).
  * **\[P2]** Label printing (ZPL) for cases/pallets.
  * **\[Later]** Carrier webhooks/API, warehouse systems (WMS/ERP) connectors.

---

# Frontend implementation checklist (your stack)

* **Routes (`app.routes.ts`)**

  * **\[MVP]** `/products`, `/batches`, `/packs`, `/shipments`, `/events`, `/trace/:serial`, `/devices` (P2), `/excursions` (P2).
  * Keep wildcard redirect to `/`.

* **Features structure**

  * `features/products` (list/detail + create)
  * `features/batches` (list/detail + serialize)
  * `features/packs` (search + aggregation tree)
  * `features/shipments` (wizard + detail)
  * `features/events` (timeline)
  * `features/trace` (timeline + integrity + telemetry overlay)
  * `features/devices` (P2)
  * `features/excursions` (P2)

* **Shared components**

  * **\[MVP]** `Badge`, `StatusChip`, `IntegrityPill`, `KpiCard`, `AggregationTree`, `QrCode`, `DataMatrix`.
  * **\[P2]** `TelemetryChart`, `MapTrace`.

* **Core services**

  * **\[MVP]** `AuthService`, `ApiService` (typed fetch + error handling), `ToastService`.
  * **\[MVP]** `BlockchainService` (read on-chain by ref), `HashService` (canonicalize+SHA-256).
  * **\[P2]** `DeviceService`, `ExcursionService`.

* **Guards & interceptors**

  * **\[MVP]** `authGuard`, `jwtInterceptor` (refresh on 401), global error interceptor.

---

# Testing & QA

* **\[MVP]** Backend unit tests for hashing, event creation, anchoring stub; API contract tests.
* **\[MVP]** Frontend unit tests for shared components; e2e (Playwright) for core flows.
* **\[P2]** Hardware-in-the-loop tests: simulated sensor traces → excursion detection.
* **\[P2]** Audit/trace export reproducibility test (recompute hashes match anchored).

---

# DevOps & environments

* **\[MVP]** Docker for backend + Postgres; Vite dev server proxy to `/api`.
* **\[MVP]** Migrations, seed data (demo products, batches, serials).
* **\[P2]** CI/CD (lint, tests, build, migrations); secrets via `.env` templates.
* **\[P2]** Observability: structured logs, health checks, uptime alerts.
* **\[Later]** Device fleet dashboard (provisioning stats, OTA success rate).

---

# Suggested MVP slice (build order)

1. **Products/Batches/Packs** (serialize + print QR/DataMatrix)
2. **Shipments** (add packs, dispatch, receive)
3. **Events & Trace** (timeline + integrity badge)
4. **ESP32 Telemetry Ingestion** (basic temp/humidity to shipment)
5. **Blockchain Anchoring** (hash + tx + verify UI)
6. **Cold-chain Rules & Excursions** (alerts + disposition)

---

If you want, I can turn this into a **ready-to-import ticket list** (CSV/JSON), plus stub Angular routes and DRF serializers/views to jump-start the scaffolding.
