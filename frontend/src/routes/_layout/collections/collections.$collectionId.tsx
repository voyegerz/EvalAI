import {
  Box,
  Container,
  Heading,
  Table,
  Text,
  Badge,
  Grid,
  GridItem,
  Button,
  Flex,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import {
  getAnsPdfsByCollectionQueryOptions,
  getCollectionQueryOptions,
  getQpPdfsByCollectionQueryOptions,
} from "@/hooks/queryOptions";
import PdfViewer from "@/components/Collections/PdfViewer";
import AddAnsPdf from "@/components/Collections/AddAnsPdf";
import StartEvaluation from "@/components/Collections/StartEvaluation";
import AddQpPdf from "@/components/Collections/AddQpPdf";
import ViewEvaluation from "@/components/Collections/ViewEvaluation"; // 1. Import the new component
import { CollectionsReadCollectionResponse } from "@/client";

// Corrected route path
export const Route = createFileRoute("/_layout/collections/collections/$collectionId")({
  component: CollectionDetail,
});

function CollectionDetail() {
  const { collectionId } = Route.useParams();
  const [viewing, setViewing] = useState<{ type: "ans" | "qp"; id: string } | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const {
    data: collection,
    isLoading: isCollectionLoading,
  } = useQuery<CollectionsReadCollectionResponse, Error>({
    ...getCollectionQueryOptions(collectionId),
    refetchInterval: isEvaluating ? 5000 : false,
  });

  collection?.is_evaluated && isEvaluating && setIsEvaluating(false);
  const { data: ansPdfsData, isLoading: arePdfsLoading } = useQuery(
    getAnsPdfsByCollectionQueryOptions(collectionId)
  );
  const { data: qpPdfsData, isLoading: isQpLoading } = useQuery(
    getQpPdfsByCollectionQueryOptions(collectionId)
  );

  if (isCollectionLoading || arePdfsLoading || isQpLoading) {
    return <p>Loading collection details...</p>;
  }

  const ansPdfs = ansPdfsData?.data ?? [];
  const questionPaper = qpPdfsData?.data?.[0];

  return (
    <Container maxW="full" pt={8}>
      <Flex justifyContent="space-between" alignItems="center" mb={6}>
        <Box>
          <Heading size="lg">{collection?.name}</Heading>
          <Text fontSize="lg" color="gray.500" mt={1}>
            <Badge
              mr={2}
              colorPalette={collection?.is_evaluated ? "green" : "gray"}
            >
              {collection?.is_evaluated ? "Evaluated" : "Pending"}
            </Badge>
            {ansPdfs.length} Answer Sheet(s)
          </Text>
        </Box>
        <Flex gap={4}>
          {questionPaper && (
            <Button
              onClick={() => setViewing({ type: "qp", id: questionPaper.id })}
              variant="outline"
            >
              View Question Paper
            </Button>
          )}
          <AddQpPdf collectionId={collectionId} />
          {collection && (
            <StartEvaluation
              collection={collection}
              isEvaluating={isEvaluating}
              onEvaluationStart={() => setIsEvaluating(true)}
            />
          )}
        </Flex>
      </Flex>

      <Grid templateColumns="450px 1fr" gap={6} h="calc(100vh - 220px)">
        <GridItem overflowY="auto" pr={2}>
          <Flex justifyContent="space-between" alignItems="center" mb={4}>
            <Heading size="md">Answer Sheets</Heading>
            <AddAnsPdf collectionId={collectionId} />
          </Flex>
          <Table.Root size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>File Name</Table.ColumnHeader>
                {/* 2. Add a new column for the action */}
                <Table.ColumnHeader>Results</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {ansPdfs.map((pdf) => (
                <Table.Row
                  key={pdf.id}
                  onClick={() => setViewing({ type: "ans", id: pdf.id })}
                  cursor="pointer"
                  bg={
                    viewing?.type === "ans" && viewing?.id === pdf.id
                      ? "blue.50"
                      : "transparent"
                  }
                  _dark={{
                    bg:
                      viewing?.type === "ans" && viewing?.id === pdf.id
                        ? "blue.900"
                        : "transparent",
                  }}
                  _hover={{
                    bg: "gray.100",
                    _dark: { bg: "gray.700" },
                  }}
                >
                  <Table.Cell
                    fontWeight={
                      viewing?.type === "ans" && viewing?.id === pdf.id
                        ? "bold"
                        : "medium"
                    }
                  >
                    {pdf.name}
                  </Table.Cell>
                  {/* 3. Add a new cell for the ViewEvaluation button */}
                  <Table.Cell onClick={(e) => e.stopPropagation()}>
                    {collection?.is_evaluated && (
                      <ViewEvaluation pdf={pdf} collectionId={collectionId} />
                    )}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </GridItem>
        <GridItem>
          <PdfViewer viewing={viewing} collectionId={collectionId} />
        </GridItem>
      </Grid>
    </Container>
  );
}