import * as XLSX from "xlsx";

export async function fetchXLSFromURL(url: string) {
  try {
    url = url.replace("5173", "8290");
    //url = `http://localhost:8290${url}`
    console.log(`fetching: ${url}`);
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    const workbook = convertDataToWorkbook(arrayBuffer);
    return workbook;

    //const workbook = XLSX.read(arrayBuffer, { type: 'array', cellFormula: true, cellStyles: true });
    // return workbook.SheetNames.map(sheetName => ({
    // 	name: sheetName,
    // 	data: XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 })
    // }));
  } catch (err) {
    const msg = `error: ${JSON.stringify(err)}`;
    console.error(`Error fetching XLS file: ${msg}`);
  }
}

// read the raw data and convert it to a XLSX workbook
function convertDataToWorkbook(dataRows: ArrayBuffer) {
  /* convert data to binary string */
  const data = new Uint8Array(dataRows);
  const arr = [];

  for (let i = 0; i !== data.length; ++i) {
    arr[i] = String.fromCharCode(data[i]);
  }

  const bstr = arr.join("");

  return XLSX.read(bstr, { type: "binary" });
}
