terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {
    bucket = "gcp-student-project-480912-tf-state"
    prefix = "terraform/state"
  }
}

variable "gcp_project_id" {
  description = "The GCP project ID."
  default     = "gcp-student-project-480912"
}

variable "gcp_region" {
  description = "The GCP region where resources will be created."
  default     = "europe-central2"
}

provider "google" {
  user_project_override       = true
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google" {
  alias                       = "seed"
  user_project_override       = false
  region                      = var.gcp_region
}

resource "google_project_service" "cloud_serviceusage_api" {
  provider                   = google.seed
  project                    =  var.gcp_project_id
  service                    = "serviceusage.googleapis.com"
  disable_dependent_services = false
}

resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
  depends_on = [google_project_service.cloudresourcemanager]
  disable_on_destroy= true
  disable_dependent_services=true
}


resource "google_project_service" "cloudresourcemanager" {
  depends_on                 = [google_project_service.cloud_serviceusage_api]
  provider                   = google.seed
  project                    =  var.gcp_project_id
  service                    = "cloudresourcemanager.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy= false
}

resource "google_project_service" "pubsub" {
  service = "pubsub.googleapis.com"
  depends_on = [google_project_service.cloudresourcemanager]
  #disable_on_destroy= false
  disable_dependent_services=true
}

resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
  depends_on = [google_project_service.cloudresourcemanager]
}

resource "google_project_service" "monitoring" {
  service = "monitoring.googleapis.com"
  depends_on = [google_project_service.cloudresourcemanager]
  disable_dependent_services=false
}

resource "google_project_service" "run" {
  service    = "run.googleapis.com"
  depends_on = [google_project_service.cloudresourcemanager]
}


resource "google_firestore_database" "database" {
  project = var.gcp_project_id
  name    = "(default)"
  location_id = var.gcp_region
  type    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_ENABLED"
  depends_on = [google_project_service.cloudresourcemanager]

}


resource "google_pubsub_topic" "new_entry" {
  name = "new-entries"
  depends_on = [google_project_service.pubsub]
}

# --- Konfiguracja usługi Cloud Run ---

resource "google_cloud_run_v2_service" "default" {
  name     = "myapp" 
  location = var.gcp_region

  
  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"  #"europe-central2-docker.pkg.dev/${var.gcp_project_id}/myapp-repo/myapp:latest" #
    }
    service_account = google_service_account.myapp_sa.email
  }
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.run,
    google_project_service.cloudbuild,
    google_project_iam_member.run_service_monitoring, # Upewnij się, że uprawnienia są nadane przed startem usługi
    google_project_iam_member.run_service_pubsub,
    google_project_iam_member.run_service_datastore,
  ]
}

# --- Dedykowane konto serwisowe dla aplikacji ---

resource "google_service_account" "myapp_sa" {
  account_id   = "myapp-sa"
  display_name = "Service Account for myapp Cloud Run"
}

# --- Uprawnienia dla usługi Cloud Run ---

# 1. Pozwolenie na publiczny, nieuwierzytelniony dostęp do usługi
resource "google_cloud_run_service_iam_member" "allow_unauthenticated" {
  location = google_cloud_run_v2_service.default.location
  project  = google_cloud_run_v2_service.default.project
  service  = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 2. Nadanie uprawnień dedykowanemu kontu serwisowemu
data "google_project" "project" {}

resource "google_project_iam_member" "run_service_datastore" {
  project = var.gcp_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.myapp_sa.email}"
}

resource "google_project_iam_member" "run_service_pubsub" {
  project = var.gcp_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.myapp_sa.email}"
  
}

resource "google_project_iam_member" "run_service_monitoring" {
  project = var.gcp_project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.myapp_sa.email}"
}