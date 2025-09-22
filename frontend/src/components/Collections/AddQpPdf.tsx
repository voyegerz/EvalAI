import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Input, Text } from "@chakra-ui/react";
import { FiUpload } from "react-icons/fi";

import { UploadService, type ApiError } from "@/client";
import useCustomToast from "@/hooks/useCustomToast";
import { handleError } from "@/utils";
import { Button } from "@/components/ui/button";
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";

interface AddQpPdfProps {
  collectionId: string;
}

const AddQpPdf = ({ collectionId }: AddQpPdfProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();

  const mutation = useMutation({
    mutationFn: (file: File) => {
      const formData = {
        file: file,
        collection_id: collectionId,
      };
      // Call the specific service for uploading question papers
      return UploadService.uploadQppdf({ formData });
    },
    onSuccess: () => {
      showSuccessToast("Question Paper uploaded successfully.");
      // Invalidate the query for this collection's question papers to refresh the page
      queryClient.invalidateQueries({
        queryKey: ["collections", collectionId, "qpPdfs"],
      });
      setSelectedFile(null);
      setIsOpen(false);
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const onSubmit = () => {
    if (selectedFile) {
      mutation.mutate(selectedFile);
    }
  };

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
      size={{ base: "xs", md: "md" }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">Upload Question Paper</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Question Paper</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <Text mb={4}>Select the question paper PDF for this collection.</Text>
          <Field label="PDF File" required>
            <Input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              p={1}
            />
          </Field>
        </DialogBody>
        <DialogFooter gap={2}>
          <Button
            variant="subtle"
            onClick={() => setIsOpen(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            variant="solid"
            onClick={onSubmit}
            loading={mutation.isPending}
            disabled={!selectedFile}
          >
            <FiUpload style={{ marginRight: 8 }} />
            Upload
          </Button>
        </DialogFooter>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default AddQpPdf;