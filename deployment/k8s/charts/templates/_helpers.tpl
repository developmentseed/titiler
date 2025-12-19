{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "titiler.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "titiler.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "titiler.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "titiler.labels" -}}
helm.sh/chart: {{ include "titiler.chart" . }}
{{ include "titiler.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "titiler.selectorLabels" -}}
app.kubernetes.io/name: {{ include "titiler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Helpers for titiler_xarray.
These reuse the titiler helpers and simply append "-xarray".
*/}}

{{- define "titiler_xarray.name" -}}
{{- printf "%s-xarray" (include "titiler.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "titiler_xarray.fullname" -}}
{{- printf "%s-xarray" (include "titiler.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "titiler_xarray.selectorLabels" -}}
app.kubernetes.io/name: {{ include "titiler_xarray.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "titiler_xarray.labels" -}}
helm.sh/chart: {{ include "titiler.chart" . }}
{{ include "titiler_xarray.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
