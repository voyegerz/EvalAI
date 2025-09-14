import {
  Flex,
  Image,
  Text,
  TextStyles,
  useBreakpointValue,
} from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";

import Logo from "/assets/images/fastapi-logo.svg";
import UserMenu from "./UserMenu";

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" });

  return (
    <Flex
      display={display}
      justify="space-between"
      position="sticky"
      color="white"
      align="center"
      bg="bg.muted"
      w="100%"
      top={0}
      p={4}
      rounded={"lg"}
      mb={2}
    >
      <Link to="/">
        <Text
          textStyle="4xl"
          fontWeight={"bold"}
          color="black"
          _dark={{
            color: "white",
          }}
        >
          Eval
          <Text as="span" color="blue.500">
            AI
          </Text>
        </Text>
      </Link>
      <Flex gap={2} alignItems="center">
        <UserMenu />
      </Flex>
    </Flex>
  );
}

export default Navbar;
