export const logger = console;

function extractLineNumber(text: string): string | null {
  const regex = /(\d+):\d+\)\]$/;
  const match = text.match(regex);
  return match ? match[1] : null;
}

export function logWithTimestamp(message: string) {
  const now = new Date(); // Create a new Date object containing the current date and time
  const timestamp = now.toISOString(); // Convert the current date and time to a string in ISO format
  const error = new Error();
  const stack = error.stack;
  if (stack) {
    const callerLine = stack.split("\n")[2];
    const lineNumber = extractLineNumber(callerLine);
    const callerName = callerLine.match(/at (\w+)/)?.[1];
    if (lineNumber !== null) {
      logger.log(`[${timestamp}](${callerName}[${lineNumber}]) ${message}`); // Log the message with the timestamp
    } else {
      logger.log(`[${timestamp}](${callerName}[]) ${message}`); // Log the message with the timestamp
    }
  } else {
    logger.log(`[${timestamp}] ${message}`); // Log the message with the timestamp
  }
}
