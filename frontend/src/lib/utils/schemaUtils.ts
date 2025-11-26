import { EnumSchemaVersions } from "gaia-api";

export const getEnumPosition = (value: EnumSchemaVersions): number => {
  const enumValues = Object.values(EnumSchemaVersions);
  return enumValues.indexOf(value) + 1;
};

const getEnumPositionMap = (): Record<EnumSchemaVersions, number> => {
  const enumValues = Object.values(EnumSchemaVersions);
  return Object.fromEntries(
    enumValues.map((value, index) => [value, index]),
  ) as Record<EnumSchemaVersions, number>;
};
const ENUM_POSITIONS = getEnumPositionMap();

export const getPositionFromString = (value: string): number | undefined => {
  // Type check if the string is a valid enum value
  if (value in EnumSchemaVersions) {
    return ENUM_POSITIONS[value as EnumSchemaVersions];
  }
  return undefined;
};
