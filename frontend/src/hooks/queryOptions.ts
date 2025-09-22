import { CollectionsService, EvaluationsService, UploadService } from "@/client";

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

export function getQpPdfsByCollectionQueryOptions(collectionId: string) {
  return {
    queryFn: () => UploadService.getQppdfsByCollection({ collectionId }),
    queryKey: ["collections", collectionId, "qpPdfs"],
  };
}
export function getAnsPdfBlobQueryOptions(pdfId: string) {
  return {
    queryFn: async (): Promise<Blob> => {
      const response = await fetch(`http://localhost:8000/api/v1/download/ans-pdfs/${pdfId}/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`, // if needed
        },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch PDF");
      }
      return await response.blob(); // ✅ true Blob, not base64 string
    },
    queryKey: ["ansPdfs", pdfId, "blob"],
    staleTime: Infinity,
  };
}

export function getQpPdfBlobQueryOptions(collectionId: string) {
  return {
    queryFn: async (): Promise<Blob> => {
      const response = await fetch(`http://localhost:8000/api/v1/download/qppdfs/${collectionId}/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`, // if needed
        },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch PDF");
      }
      return await response.blob();
    },
    queryKey: ["qpPdfs", collectionId, "blob"],
    staleTime: Infinity,
  };
}

export function getEvaluationsByCollectionQueryOptions(collectionId: string) {
  return {
    queryFn: () => EvaluationsService.readEvaluationsByCollection({ collectionId }),
    queryKey: ["collections", collectionId, "evaluations"],
  };
}