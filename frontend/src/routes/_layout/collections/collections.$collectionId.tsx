import {
  Box,
  Container,
  Heading,
  Table,
  Text,
  Badge,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import {
  getAnsPdfsByCollectionQueryOptions,
  getCollectionQueryOptions,
} from "@/hooks/queryOptions";

export const Route = createFileRoute("/_layout/collections/collections/$collectionId")({
  component: CollectionDetail,
});

function CollectionDetail() {
  const { collectionId } = Route.useParams();

  const { data: collectionData, isLoading: isCollectionLoading } = useQuery(
    getCollectionQueryOptions(collectionId)
  );
  const { data: ansPdfsData, isLoading: arePdfsLoading } = useQuery(
    getAnsPdfsByCollectionQueryOptions(collectionId)
  );

  if (isCollectionLoading || arePdfsLoading) {
    return <p>Loading collection details...</p>;
  }

  const collection = collectionData;
  const ansPdfs = ansPdfsData?.data ?? [];

  return (
    <Container maxW="full" pt={12}>
      <Box>
        <Heading size="lg">{collection?.name}</Heading>
        <Text fontSize="lg" color="gray.500" mt={1}>
          Answer Sheets
          <Badge ml={2} colorPalette={collection?.is_evaluated ? "green" : "gray"}>
            {collection?.is_evaluated ? "Evaluated" : "Pending"}
          </Badge>
        </Text>
      </Box>

      <Table.Root mt={8} size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>File Name</Table.ColumnHeader>
            {/* Add more columns as needed, e.g., for scores */}
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {ansPdfs.map((pdf) => (
            <Table.Row key={pdf.id}>
              <Table.Cell fontWeight="medium">{pdf.name}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Container>
  );
}