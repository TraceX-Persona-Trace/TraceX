/**
 * Formats a date string into Indian Standard Time (Asia/Kolkata) using
 * Intl.DateTimeFormat with locale 'en-IN'.
 * Returns a formatted string or a fallback placeholder when the input is
 * missing or invalid.
 */
export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return '';
  try {
    const formatter = new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      dateStyle: 'medium',
      timeStyle: 'medium',
    });
    return formatter.format(date);
  } catch (_) {
    // Fallback to ISO string if Intl fails for any reason
    return date.toISOString();
  }
}
