import { CollectionsService, UploadService } from "@/client";

// Corrected this function to use readCollections
export function getCollectionsQueryOptions() {
  return {
    queryFn: () => CollectionsService.readCollections(),
    queryKey: ["collections"],
  };
}

export function getCollectionQueryOptions(collectionId: string) {
  return {
    queryFn: () => CollectionsService.readCollection({ id: collectionId }),
    queryKey: ["collections", collectionId],
  };
}

export function getAnsPdfsByCollectionQueryOptions(collectionId: string) {
  return {
    queryFn: () => UploadService.getAnsPdfsByCollection({ collectionId }),
    queryKey: ["collections", collectionId, "ansPdfs"],
  };
}