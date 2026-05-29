// Coerce anything (string / number / object / null / undefined) into a string
// safe for React to render. Used at every render site that consumes
// LLM-generated JSON, since the model may return objects where we expect strings.
export function toText(value) {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}
