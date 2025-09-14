import {
  Badge, 
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  VStack,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import {  Link as RouterLink, createFileRoute } from "@tanstack/react-router";
import { FiSearch } from "react-icons/fi";

// --- 1. Import the new components ---
import AddCollection from "@/components/Collections/AddCollection";
import { CollectionActionsMenu } from "@/components/Collections/CollectionActionsMenu";
import { type CollectionsReadCollectionsResponse } from "@/client";
import { getCollectionsQueryOptions } from "@/hooks/queryOptions";

export const Route = createFileRoute("/_layout/collections/")({
  component: Collections,
});

function CollectionsTable() {
  const { data, isLoading } = useQuery<CollectionsReadCollectionsResponse>(
    getCollectionsQueryOptions()
  );

  const collections = data?.data ?? [];

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (collections.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>You don't have any collections yet</EmptyState.Title>
            <EmptyState.Description>
              Add a new collection to get started
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    );
  }

  return (
    <Table.Root size={{ base: "sm", md: "md" }}>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader w="sm">Name</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Branch</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">School</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Department</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Status</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Actions</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {collections.map((collection) => (
          <Table.Row key={collection.id}>
            <Table.Cell
              fontWeight="medium"
              _hover={{ textDecoration: "underline", color: "blue.500" }}
            >
              <RouterLink
                to="/collections/collections/$collectionId"
                params={{ collectionId: collection.id }}
                style={{ textDecoration: "none" }} // Prevent default underline on router link
              >
                <Flex
                  as="span" // Render as a span, not another link
                  _hover={{ textDecoration: "underline", color: "blue.500" }}
                >
                  {collection.name}
                </Flex>
              </RouterLink>
            </Table.Cell>
            <Table.Cell>{collection.branch || "N/A"}</Table.Cell>
            <Table.Cell>{collection.school || "N/A"}</Table.Cell>
            <Table.Cell>{collection.department || "N/A"}</Table.Cell>
            <Table.Cell>
              {collection.is_evaluated ? (
                <Badge colorPalette="green">Evaluated</Badge>
              ) : (
                <Badge colorPalette="red">Pending</Badge>
              )}
            </Table.Cell>
            <Table.Cell>
              <CollectionActionsMenu collection={collection} />
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  );
}

function Collections() {
  return (
    <Container maxW="full">
      <Flex justifyContent="space-between" alignItems="center" pt={12}>
        <Heading size="lg">Collections Management</Heading>
        {/* --- 2. Replace the static button with the AddCollection component --- */}
        <AddCollection />
      </Flex>
      <CollectionsTable />
    </Container>
  );
}