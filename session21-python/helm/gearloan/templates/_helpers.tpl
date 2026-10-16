{{/* Chart name, can be overridden with nameOverride */}}
{{- define "gearloan.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Release-based name used as a prefix for every object */}}
{{- define "gearloan.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "gearloan.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Labels on every object */}}
{{- define "gearloan.labels" -}}
helm.sh/chart: {{ include "gearloan.chart" . }}
app.kubernetes.io/name: {{ include "gearloan.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: gearloan
{{- end }}

{{/* Selector labels. Call with (dict "ctx" . "component" "backend") */}}
{{- define "gearloan.selectorLabels" -}}
app.kubernetes.io/name: {{ include "gearloan.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/* Object names for each part */}}
{{- define "gearloan.backend.fullname" -}}
{{- printf "%s-backend" (include "gearloan.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- define "gearloan.frontend.fullname" -}}
{{- printf "%s-frontend" (include "gearloan.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- define "gearloan.postgres.fullname" -}}
{{- printf "%s-postgres" (include "gearloan.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "gearloan.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "gearloan.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image reference. Call with (dict "ctx" . "image" .Values.backend.image).
Empty registry gives a plain name like "gearloan-backend:local" (minikube).
Empty tag falls back to the chart appVersion.
*/}}
{{- define "gearloan.image" -}}
{{- $registry := .ctx.Values.image.registry | default "" | trimSuffix "/" }}
{{- $tag := .image.tag | default .ctx.Chart.AppVersion | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry .image.repository $tag }}
{{- else }}
{{- printf "%s:%s" .image.repository $tag }}
{{- end }}
{{- end }}

{{/* Secret holding the DB password */}}
{{- define "gearloan.postgres.secretName" -}}
{{- if .Values.postgres.existingSecret }}
{{- .Values.postgres.existingSecret }}
{{- else }}
{{- printf "%s-db" (include "gearloan.fullname" .) }}
{{- end }}
{{- end }}

{{/* Host the backend connects to */}}
{{- define "gearloan.postgres.host" -}}
{{- if .Values.postgres.enabled }}
{{- include "gearloan.postgres.fullname" . }}
{{- else }}
{{- required "postgres.externalHost is required when postgres.enabled is false" .Values.postgres.externalHost }}
{{- end }}
{{- end }}

{{/* Backend version shown in /api/info */}}
{{- define "gearloan.backend.appVersion" -}}
{{- .Values.backend.appVersion | default .Chart.AppVersion | toString }}
{{- end }}
