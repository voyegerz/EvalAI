import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FiPlayCircle } from "react-icons/fi";

import {
  EvaluateService,
  type CollectionPublic,
  type ApiError,
} from "@/client";
import useCustomToast from "@/hooks/useCustomToast";
import { handleError } from "@/utils";
import { Button } from "@/components/ui/button";

interface StartEvaluationProps {
  collection: CollectionPublic;
  onEvaluationStart: () => void; // A function to notify the parent page
  isEvaluating: boolean;
}

const StartEvaluation = ({
  collection,
  onEvaluationStart,
  isEvaluating,
}: StartEvaluationProps) => {
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();

  const mutation = useMutation({
    mutationFn: () =>
      EvaluateService.evaluateAnswersheet({ collectionId: collection.id }),
    onSuccess: () => {
      showSuccessToast(
        "Evaluation started! The process is running in the background."
      );
      // Call the function passed from the parent to start polling
      onEvaluationStart();
      // Invalidate queries to get the initial "processing" state if any
      queryClient.invalidateQueries({
        queryKey: ["collections", collection.id],
      });
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
  });

  const isDisabled =
    collection.is_evaluated || mutation.isPending || isEvaluating;
  const buttonText = collection.is_evaluated
    ? "Evaluation Complete"
    : isEvaluating
      ? "Evaluating..."
      : "Start Evaluation";

  return (
    <Button
      onClick={() => mutation.mutate()}
      colorScheme="green"
      loading={mutation.isPending || isEvaluating}
      disabled={isDisabled}
    >
      <FiPlayCircle style={{ marginRight: 8 }} />
      {buttonText}
    </Button>
  );
};

export default StartEvaluation;
