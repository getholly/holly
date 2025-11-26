import { writable } from "svelte/store";
import { persistableStore } from "./persistable.store";
import type { RepoSelection } from "$lib/types/githubTypes";

// Store for wizard state - ensure proper initialization
export const wizardBranchName = persistableStore("wizardBranchName", "");
export const wizardSelectedRepos = persistableStore<RepoSelection[]>(
  "wizardSelectedRepos",
  [],
);
export const wizardSelectedLlm = persistableStore("wizardSelectedLlm", "");
export const wizardSelectedTools = persistableStore<string[]>(
  "wizardSelectedTools",
  [],
);
export const wizardSelectedKnowledge = persistableStore<string[]>(
  "wizardSelectedKnowledge",
  [],
);
export const wizardDescription = persistableStore("wizardDescription", "");

const STARTING_WIZARD_INDEX = 1; // Flowbite-svelte StepIndicator starts at 1
export const wizardActiveStep = writable(STARTING_WIZARD_INDEX);

// Reset all wizard data
export function resetWizard() {
  wizardBranchName.set("");
  wizardSelectedRepos.set([]);
  wizardSelectedLlm.set("");
  wizardSelectedTools.set([]);
  wizardSelectedKnowledge.set([]);
  wizardDescription.set("");
  wizardActiveStep.set(STARTING_WIZARD_INDEX); // ✅ Reset to proper starting index
}

// Debug function to check store values
export function debugWizardStores() {
  console.log("Wizard Store Debug:", {
    branchName: wizardBranchName,
    selectedRepos: wizardSelectedRepos,
    selectedLlm: wizardSelectedLlm,
    activeStep: wizardActiveStep,
  });
}
