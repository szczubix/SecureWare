import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleString('pl-PL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function formatDateShort(date: Date | string): string {
  return new Date(date).toLocaleDateString('pl-PL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

export const SEVERITY_LABELS: Record<string, string> = {
  CRITICAL: 'Krytyczny', HIGH: 'Wysoki', MEDIUM: 'Średni', LOW: 'Niski',
}
export const STATUS_LABELS: Record<string, string> = {
  NEW: 'Nowy', IN_PROGRESS: 'W toku', ANALYSIS: 'Analiza', CLOSED: 'Zamknięty',
}
export const CATEGORY_LABELS: Record<string, string> = {
  UNAUTHORIZED_ACCESS: 'Nieautoryzowany dostęp', DATA_LEAK: 'Wyciek danych',
  AVAILABILITY: 'Niedostępność', PHISHING: 'Phishing',
  MALWARE: 'Złośliwe oprogramowanie', PHYSICAL: 'Incydent fizyczny', OTHER: 'Inne',
}
export const ASSET_TYPE_LABELS: Record<string, string> = {
  HARDWARE: 'Sprzęt', SOFTWARE: 'Oprogramowanie', DATA: 'Dane',
  CLOUD_SERVICE: 'Usługa cloud', INFRASTRUCTURE: 'Infrastruktura', OTHER: 'Inne',
}
export const CLASSIFICATION_LABELS: Record<string, string> = {
  PUBLIC: 'Publiczny', INTERNAL: 'Wewnętrzny',
  CONFIDENTIAL: 'Poufny', RESTRICTED: 'Zastrzeżony',
}
