import { writable, derived } from "svelte/store";
import type { RepoSelection } from "$lib/types/githubTypes";

// All selected repositories (from GitMultiSelect)
export const selectedRepoSelections = writable<RepoSelection[]>([]);

// Primary selection: the first repo with a selected branch
export const primaryRepoFullName = derived(selectedRepoSelections, ($list) => {
  const first = $list.find((s) => !!s.selectedBranch);
  return first ? first.repo.full_name : null;
});

export const primaryBranchName = derived(selectedRepoSelections, ($list) => {
  const first = $list.find((s) => !!s.selectedBranch);
  return first ? first.selectedBranch : null;
});

export function setSelections(selections: RepoSelection[]) {
  selectedRepoSelections.set(selections || []);
}
