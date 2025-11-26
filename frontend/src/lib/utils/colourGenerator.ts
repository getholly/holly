export function getColor(index: number) {
  const colors = ["blue", "green", "red", "yellow", "indigo", "purple", "pink"];
  return colors[index % colors.length];
}
