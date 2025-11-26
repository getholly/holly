import type { ContractType, Shipment } from "gaia-api";

export function sortItems(
  items: ContractType[],
  sortKey: keyof ContractType,
  sortDirection: number,
): ContractType[] {
  return [...items].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    return aVal < bVal ? -sortDirection : aVal > bVal ? sortDirection : 0;
  });
}

export function sortShipments(
  items: Shipment[],
  sortKey: keyof Shipment,
  sortDirection: number,
): Shipment[] {
  return [...items].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    return aVal < bVal ? -sortDirection : aVal > bVal ? sortDirection : 0;
  });
}

// we can use this function to replace the 2 above
export function sortItemsGeneric<T>(
  items: T[],
  sortKey: keyof T,
  sortDirection: number,
): T[] {
  return [...items].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    return aVal < bVal ? -sortDirection : aVal > bVal ? sortDirection : 0;
  });
}
