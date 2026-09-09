import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as researchApi from "../api/research";
import type { ResearchRequest } from "../api/types";

export function useResearches() {
  return useQuery({ queryKey: ["research"], queryFn: researchApi.listResearch });
}

export function useCreateResearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ResearchRequest) => researchApi.createResearch(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["research"] }),
  });
}

export function useDeleteResearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (researchId: string) => researchApi.deleteResearch(researchId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["research"] }),
  });
}
