import { Box, Spinner, Text, VStack } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import {
  getAnsPdfBlobQueryOptions,
  getQpPdfBlobQueryOptions,
} from "@/hooks/queryOptions";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

interface PdfViewerProps {
  viewing: { type: "ans" | "qp"; id: string } | null;
  collectionId: string;
}

const PdfViewer = ({ viewing, collectionId }: PdfViewerProps) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  const ansPdfQuery = useQuery<Blob, Error>({
    ...getAnsPdfBlobQueryOptions(viewing?.id || ""),
    enabled: !!viewing && viewing.type === "ans",
  });

  const qpPdfQuery = useQuery<Blob, Error>({
    ...getQpPdfBlobQueryOptions(collectionId),
    enabled: !!viewing && viewing.type === "qp",
  });

  const currentQuery = viewing?.type === "ans" ? ansPdfQuery : qpPdfQuery;

  useEffect(() => {
    if (currentQuery.data) {
      const url = URL.createObjectURL(currentQuery.data);
      setPdfUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [currentQuery.data]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }): void {
    setNumPages(numPages);
  }

  if (!viewing) {
    return (
      <Box p={4} borderWidth="1px" borderRadius="md" h="100%">
        <Text>Select an Answer Sheet or the Question Paper to view it.</Text>
      </Box>
    );
  }

  return (
    <Box
      p={2}
      borderWidth="1px"
      borderRadius="md"
      h="100%"
      overflowY="auto"
      bg="gray.50"
      _dark={{ bg: "gray.700" }}
    >
      {currentQuery.isLoading && <Spinner />}
      {currentQuery.isError && (
        <Text color="red.500">Failed to load PDF file.</Text>
      )}
      {pdfUrl && (
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<Spinner />}
        >
          <VStack gap={4}>
            {Array.from(new Array(numPages), (_, index) => (
              <Page
                key={`page_${index + 1}`}
                pageNumber={index + 1}
                renderTextLayer={true}   // ✅ shows text
                renderAnnotationLayer={true} // ✅ supports highlights/links
                width={800}
              />
            ))}
          </VStack>
        </Document>
      )}
    </Box>
  );
};

export default PdfViewer;
