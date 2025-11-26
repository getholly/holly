import { writable } from "svelte/store";
import type { MissionDetail } from "holly-api";

export const currentMission = writable<MissionDetail | null>(null);
