// generate a unique key given a dict and an existing key
export function generateUniqueKey(
  dict: { [key: string]: any },
  existingKey: string,
) {
  const alphabet = "abcdefghijklmnopqrstuvwxyz";
  let uniqueKey = existingKey;
  let index = 0;
  let combination = "";

  while (dict.hasOwnProperty(uniqueKey)) {
    if (index === alphabet.length) {
      index = 0;
      combination += alphabet[0];
    }

    uniqueKey = existingKey + combination + alphabet[index];
    index++;
  }

  return uniqueKey;
}

export const metalsSortOrder = [
  "Cu",
  "Pb",
  "Zn",
  "Sn",
  "Ni",
  "Ag",
  "Au",
  "Pd",
  "Pb",
];

type NestedDict = {
  [key: string]: boolean | NestedDict;
};

// iterate though a dict and determine if it's all verified
export function checkIsVerified(
  nestedDict: any,
  verify_key: string = "verified",
  test_value: boolean = true,
): boolean {
  for (const [key, value] of Object.entries(nestedDict)) {
    if (key === verify_key) {
      if (value !== test_value) {
        return false;
      }
    } else if (typeof value === "object" && value !== null) {
      if (!checkIsVerified(value as NestedDict)) {
        return false;
      }
    }
  }
  return true;
}

// export function setAll(nestedDict: any, attr_key: string, value: any): boolean {
// 	for (const [key, value] of Object.entries(nestedDict)) {
// 		if (key === attr_key) {
// 			if (!value) {
// 				return false
// 			}
// 		} else if (typeof value === "object" && value !== null) {
// 			if (!checkIsVerified(value as NestedDict)) {
// 				return false
// 			}
// 		}
// 	}
// 	return true
// }

// Used for the updateData only
export function verifyAllUpdateDataVerifyKeys(obj: any): void {
  if (obj && typeof obj === "object") {
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const value = obj[key];
        if (value && typeof value === "object") {
          verifyAllUpdateDataVerifyKeys(value);
        }
      }
    }
    // Check if it's a leaf node (has 'val', 'pg', and 'verify' properties)
    if ("val" in obj && "pg" in obj && "verify" in obj) {
      obj.verify = true;
    }
  }
}

export function updateFields(
  nestedDict: any,
  fieldKey: string,
  newValue: any,
): NestedDict {
  for (const key in nestedDict) {
    if (key === fieldKey) {
      nestedDict[key] = newValue;
    } else if (
      typeof nestedDict[key] === "object" &&
      nestedDict[key] !== null
    ) {
      nestedDict[key] = updateFields(nestedDict[key], fieldKey, newValue);
    }
  }
  return nestedDict;
}

export function createArray<T>(length: number, value: T): T[] {
  return new Array<T>(length).fill(value);
}

export function createDictWithValues<T>(
  obj: object,
  value: T,
): { [key: string]: T } {
  const keys = Object.keys(obj);
  const entries = keys.map((key) => [key, value]);
  return Object.fromEntries(entries);
}

export function isAllVerified(obj: any): boolean {
  // Base case: if obj is null or undefined, return true
  if (obj === null || obj === undefined) {
    return true;
  }

  // If obj is an object with a 'verified' property, check its value
  if (typeof obj === "object" && "verified" in obj) {
    return obj.verified === true;
  }

  // If obj is an array, check all its elements
  if (Array.isArray(obj)) {
    return obj.every((item) => isAllVerified(item));
  }

  // If obj is an object, check all its properties
  if (typeof obj === "object") {
    return Object.values(obj).every((value) => isAllVerified(value));
  }

  // If obj is a primitive value (not an object), return true
  return true;
}

export function isObjectValuesFilled(obj: any): boolean {
  // Base case: if obj is null or undefined, return false
  if (obj === null || obj === undefined) {
    return false;
  }

  // If obj is not an object, return true (we're only checking object properties)
  if (typeof obj !== "object" || Array.isArray(obj)) {
    return true;
  }

  // Check each property of the object
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const value = obj[key];

      // If the value is an object (but not an array), skip it
      if (typeof value === "object" && !Array.isArray(value)) {
        continue;
      }

      // Check if the value is empty string, null, or undefined
      if (value === "" || value === null || value === undefined) {
        console.log(`missing ${key} / ${value}`);
        return false;
      }
    }
  }

  // If we've made it through all properties without returning false, return true
  return true;
}
