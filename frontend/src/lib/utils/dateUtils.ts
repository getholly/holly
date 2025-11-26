export function getCurrentDateTime() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${year}${month}${day} ${hours}:${minutes}`;
}

export function xformatDate(date: Date): string {
  const day: number = date.getDate();
  const month: number = date.getMonth() + 1;
  const year: number = date.getFullYear();
  // minutes and seconds only
  const time: string = date.toTimeString().slice(0, 5);

  // Pad the day and month with leading zeros if necessary
  const formattedDay = day < 10 ? "0" + day : day.toString();
  const formattedMonth = month < 10 ? "0" + month : month.toString();

  return `${year}-${formattedMonth}-${formattedDay} ${time}`;
}

function convertStringToDate(dateString: string): Date {
  // Check if the date string includes a "T" indicating time information
  if (dateString.includes("T")) {
    dateString = dateString.split("T")[0];
  }
  // Ensure the input string matches the expected format
  const datePart = dateString.split("T")[0];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
    throw new Error(`Invalid date format(${dateString}. Expected YYYY-MM-DD`);
  }

  const [year, month, day] = datePart.split("-").map(Number);

  // Note: month is 0-indexed in JavaScript Date
  return new Date(year, month - 1, day);
}

export function formatDate(
  date: Date | string,
  format: string = "%Y-%m-%d %H:%M",
): string {
  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  if (typeof date === "string") {
    date = convertStringToDate(date);
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");

  return format
    .replace(/%Y/g, year.toString())
    .replace(/%m/g, month)
    .replace(/%b/g, monthNames[date.getMonth() + 1])
    .replace(/%d/g, day)
    .replace(/%H/g, hours)
    .replace(/%M/g, minutes)
    .replace(/%S/g, seconds);
}

export function formatDateYYYYMMDD(dateString: Date) {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDateDDMMYYYYTime(date: Date): string {
  const day: number = date.getDate();
  const month: number = date.getMonth() + 1;
  const year: number = date.getFullYear();
  // minutes and seconds only
  const time: string = date.toTimeString().slice(0, 5);

  // Pad the day and month with leading zeros if necessary
  const formattedDay = day < 10 ? "0" + day : day.toString();
  const formattedMonth = month < 10 ? "0" + month : month.toString();

  return `${formattedDay}/${formattedMonth}/${year} ${time}`;
}

export function getLocaleAndAdjustTime(inputTime: Date): {
  locale: string;
  timeZone: string;
  adjustedDate: Date;
  adjustedHour: string;
} {
  // Get the browser locale
  const locale = navigator.language || "en-GB";

  // Get the time zone
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // Get the time zone offset in minutes
  const offsetMinutes = inputTime.getTimezoneOffset();

  // Create a new Date object with the offset applied
  const adjustedDate = new Date(inputTime.getTime() - offsetMinutes * 60000);

  // Format hours, minutes, and seconds
  const adjustedHour = formatTime(adjustedDate);

  return {
    locale,
    timeZone,
    adjustedDate,
    adjustedHour,
  };
}

function formatTime(date: Date): string {
  const hours = padZero(date.getHours());
  const minutes = padZero(date.getMinutes());
  const seconds = padZero(date.getSeconds());
  return `${hours}:${minutes}:${seconds}`;
}

function padZero(num: number): string {
  return num < 10 ? `0${num}` : num.toString();
}
