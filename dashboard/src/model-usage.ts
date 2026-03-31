export function getSortedModelUsage(
  modelsUsed: Record<string, number> | undefined,
): Array<[string, number]> {
  return Object.entries(modelsUsed ?? {}).sort((a, b) => b[1] - a[1]);
}
