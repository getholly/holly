export const CsvExporter = {
  arrayToCsv(data: any[]): string {
    if (data.length === 0) return "";

    const headers = Object.keys(data[0]).join(",");
    const rows = data.map((row) =>
      Object.values(row)
        .map((value) => {
          // Convert null or undefined to an empty string, otherwise convert value to string
          const safeValue =
            value === null || value === undefined ? "" : value.toString();

          // Escape double quotes by doubling them and wrap the value in double quotes
          return `"${safeValue.replace(/"/g, '""')}"`;
        })
        .join(","),
    );

    return [headers, ...rows].join("\r\n");
  },

  downloadCsv(csvContent: string, fileName: string) {
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  downloadXlsx(xlsxData: string, fileName: string) {
    // TODO: xlsx download doesn't work correctly
    const blob = new Blob([xlsxData], { type: "application/octet-stream" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  exportArrayToCsv(data: any[], fileName = "exportedData.csv") {
    const csvContent = this.arrayToCsv(data); // Convert array of objects to CSV string
    this.downloadCsv(csvContent, fileName); // Trigger download
  },
};
