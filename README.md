# System webowy na GCP z automatyzacją i observability

## Opis projektu

Projekt przedstawia prosty system webowy działający w chmurze Google Cloud Platform. Aplikacja umożliwia dodawanie danych do bazy oraz wyświetlanie istniejących rekordów poprzez minimalny interfejs użytkownika. Mimo prostej funkcjonalności, projekt koncentruje się na integracji usług chmurowych, automatyzacji infrastruktury oraz wdrożeniu observability zgodnie z dobrymi praktykami SRE/DevOps.

## Główne funkcjonalności

- Dodawanie danych do bazy poprzez prosty formularz HTML.
- Wyświetlanie listy przechowywanych danych.
- Publikacja zdarzeń po dodaniu nowego wpisu — aplikacja wysyła event do systemu kolejek.
- Asynchroniczne przetwarzanie zdarzeń — automatyczne wywołanie funkcji odpowiedzialnej za wysłanie wiadomości e-mail.
- Brak rozbudowanego frontendu — projekt skupia się na backendzie i integracji usług.

## Wykorzystane komponenty GCP

Projekt korzysta z co najmniej trzech usług Google Cloud Platform, m.in.:

- aplikacja webowa hostowana w środowisku serwerowym GCP,
- baza danych do przechowywania wpisów,
- system kolejkowy Pub/Sub,
- funkcja serverless do obsługi zdarzeń,
- magazyn obiektów do przechowywania zasobów pomocniczych,
- narzędzia logowania i monitorowania.

Szczegółowe relacje i powiązania pomiędzy komponentami zostaną przedstawione w diagramie C4 dołączonym do repozytorium.

## Observability

Projekt zapewnia podstawową obserwowalność dzięki:

- logom aplikacyjnym generowanym w backendzie,
- customowej metryce publikowanej z aplikacji (np. licznik nowych wpisów),
- możliwości zbudowania dashboardów i alertów opartych na dostępnych danych monitorujących.

## Automatyzacja infrastruktury (Terraform)

Cała infrastruktura projektu jest w pełni automatyzowana z użyciem Terraform. Repozytorium zawiera konfigurację pozwalającą uruchomić:

- **terraform apply** — utworzenie pełnej infrastruktury projektowej,
- **terraform destroy** — usunięcie wszystkich zasobów w kontrolowany sposób.

Automatyzacja zapewnia powtarzalność procesów oraz ułatwia wdrażanie kolejnych środowisk.

## Struktura repozytorium

Repozytorium zawiera:

- kod aplikacji webowej (backend + minimalny interfejs),
- konfiguracje Terraform budujące infrastrukturę,
- kod funkcji serverless obsługującej zdarzenia,
- pliki pomocnicze i konfiguracyjne.

Szczegółowy model architektury znajduje się w diagramie C4 zamieszczonym w repozytorium.

## Cele projektu

Projekt został przygotowany w celu:

- zademonstrowania integracji różnych usług GCP w jednej aplikacji,
- przedstawienia praktycznych mechanizmów automatyzacji infrastruktury,
- pokazania podstawowych możliwości observability w środowisku chmurowym,
- stworzenia minimalnego, ale kompletnego przepływu danych od użytkownika do systemów przetwarzających zdarzenia.

