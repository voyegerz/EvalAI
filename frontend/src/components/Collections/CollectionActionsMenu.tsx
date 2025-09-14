import { IconButton } from "@chakra-ui/react";
import { FiMoreVertical } from "react-icons/fi";

// --- Reverted to @/ imports ---
import { MenuContent, MenuRoot, MenuTrigger } from "@/components/ui/menu";
import type { CollectionPublic } from "@/client";
import DeleteCollection from "./DeleteCollection";
import EditCollection from "./EditCollection";
// -----------------------------

interface CollectionActionsMenuProps {
  collection: CollectionPublic;
}

export const CollectionActionsMenu = ({
  collection,
}: CollectionActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton aria-label="Options" variant="ghost">
          <FiMoreVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditCollection collection={collection} />
        <DeleteCollection collection={collection} />
      </MenuContent>
    </MenuRoot>
  );
};
