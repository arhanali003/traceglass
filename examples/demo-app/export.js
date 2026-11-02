// Small readable fixture for a static investigation. Not a packaged app.
function escapeCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function exportContacts(contacts, { includeEmail = false } = {}) {
  const columns = includeEmail ? ["name", "email"] : ["name"];
  const rows = contacts.filter(contact => !contact.archived);
  return [columns, ...rows.map(row => columns.map(key => row[key]))]
    .map(row => row.map(escapeCell).join(","))
    .join("\r\n");
}
