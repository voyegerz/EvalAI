import {
  Box,
  Heading,
  Spinner,
  Stat, // 1. Import Stat as a namespace
  Text,
  VStack,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { getEvaluationsByCollectionQueryOptions } from "@/hooks/queryOptions";
import type { AnsPdfPublic } from "@/client";

interface ViewEvaluationProps {
  pdf: AnsPdfPublic;
  collectionId: string;
}

const ViewEvaluation = ({ pdf, collectionId }: ViewEvaluationProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const {
    data: evaluationsData,
    isLoading,
    isError,
  } = useQuery({
    ...getEvaluationsByCollectionQueryOptions(collectionId),
    enabled: isOpen,
  });

  const evaluations = evaluationsData?.data ?? [];

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
      size="xl"
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          View Evaluation
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Evaluation Results for {pdf.name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {isLoading && <Spinner />}
          {isError && <Text color="red.500">Could not load results.</Text>}
          {evaluations.length > 0 ? (
            // 2. Changed 'spacing' prop to 'gap'
            <VStack gap={6} align="stretch" maxH="60vh" overflowY="auto" pr={4}>
              {evaluations.map((evaluation) => (
                <Box
                  key={evaluation.id}
                  p={4}
                  borderWidth="1px"
                  borderRadius="md"
                >
                  <Heading size="sm" mb={2}>
                    Question: {evaluation.question_no || "N/A"}
                  </Heading>
                  {/* 3. Corrected Stat component usage */}
                  <Stat.Root>
                    <Stat.Label>Marks Obtained</Stat.Label>
                    <Stat.ValueText>{evaluation.obtained_marks}</Stat.ValueText>
                    <Stat.HelpText>Max Marks: {evaluation.max_marks}</Stat.HelpText>
                  </Stat.Root>
                  <Text mt={3} fontSize="sm" color="gray.600">
                    <strong>Feedback:</strong> {evaluation.feedback}
                  </Text>
                </Box>
              ))}
            </VStack>
          ) : (
            <Text>No evaluation data found for this collection.</Text>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </DialogFooter>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default ViewEvaluation;