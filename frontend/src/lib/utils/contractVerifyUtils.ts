import { UnitsEnum, type UpdatedByUser } from "gaia-api";

// Default user object
const defaultUserObj: UpdatedByUser = {
  email: "",
  name: "",
};

export class MetalUpdateClass {
  name: { val: string; pg: number; verify: boolean };
  payment_rule: { val: string; pg: number; verify: boolean };
  amount: { val: string; pg: number; verify: boolean };
  units: { val: UnitsEnum; pg: number; verify: boolean };
  xl_formula: { val: string; pg: number; verify: boolean };

  constructor(
    name: string = "new metal",
    payment_rule: string = "New Rule",
    amount: string = "0",
    units: UnitsEnum = UnitsEnum.Kg,
    xl_formula: string = "",
  ) {
    this.name = { val: name, pg: 1, verify: false };
    this.payment_rule = { val: payment_rule, pg: 1, verify: false };
    this.amount = { val: amount, pg: 1, verify: false };
    this.units = { val: units, pg: 1, verify: false };
    this.xl_formula = { val: xl_formula, pg: 1, verify: false };
  }

  static createDefault(): MetalUpdateClass {
    return new MetalUpdateClass();
  }
}

export class ConcentrateUpdateClass {
  metals: { [key: string]: MetalUpdateClass };
  weight: { val: string; pg: number; verify: boolean };

  constructor(
    weight: string = "55",
    metals: { [key: string]: MetalUpdateClass } = {},
  ) {
    this.weight = { val: weight, pg: 1, verify: false };
    this.metals = metals;
  }

  addMetal(
    name: string,
    metal: MetalUpdateClass = MetalUpdateClass.createDefault(),
  ) {
    this.metals[name] = metal;
  }

  removeMetal(name: string) {
    delete this.metals[name];
  }

  static createDefault(): ConcentrateUpdateClass {
    return new ConcentrateUpdateClass();
  }
}

export class MetalVerifyClass {
  is_verified: boolean;
  name: {
    val: string;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };
  payment_rule: {
    val: string;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };
  amount: {
    val: string;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };
  units: {
    val: UnitsEnum;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };
  xl_formula: {
    val: string;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };

  constructor(
    userObj: UpdatedByUser = defaultUserObj,
    name: string = "new metal",
    payment_rule: string = "New Rule",
    amount: string = "0",
    units: UnitsEnum = UnitsEnum.Kg,
    xl_formula: string = "",
  ) {
    this.is_verified = false;
    this.name = {
      val: name,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
    this.payment_rule = {
      val: payment_rule,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
    this.amount = {
      val: amount,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
    this.units = {
      val: units,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
    this.xl_formula = {
      val: xl_formula,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
  }

  static createDefault(
    userObj: UpdatedByUser = defaultUserObj,
  ): MetalVerifyClass {
    return new MetalVerifyClass(userObj);
  }
}

export class ConcentrateVerifyClass {
  is_verified: boolean;
  metals: { [key: string]: MetalVerifyClass };
  weight: {
    val: string;
    pg: number;
    verified: boolean;
    verified_date: Date;
    user: UpdatedByUser;
  };

  constructor(
    userObj: UpdatedByUser = defaultUserObj,
    weight: string = "66",
    metals: { [key: string]: MetalVerifyClass } = {},
  ) {
    this.is_verified = false;
    this.metals = metals;
    this.weight = {
      val: weight,
      pg: 1,
      verified: false,
      verified_date: new Date(),
      user: userObj,
    };
  }

  addMetal(name: string, metal: MetalVerifyClass) {
    this.metals[name] = metal;
  }

  removeMetal(name: string) {
    delete this.metals[name];
  }

  static createDefault(
    userObj: UpdatedByUser = defaultUserObj,
  ): ConcentrateVerifyClass {
    return new ConcentrateVerifyClass(userObj);
  }
}
